// BITOS 06V6 / 21.01 BETA — native Win32 + Direct2D frontend.
// Build (Visual Studio Developer Command Prompt):
//   cl /std:c++17 /O2 /EHsc /utf-8 /DUNICODE /D_UNICODE NativeUI\BITOS_NativeUI.cpp /Fe:NativeUI\BITOS_NativeUI.exe d2d1.lib dwrite.lib user32.lib gdi32.lib /link /SUBSYSTEM:WINDOWS
// Place NativeUI\BITOS_Server.py beside the resulting executable. Python 3 must be on PATH.

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <windowsx.h>
#include <d2d1.h>
#include <dwrite.h>
#include <wrl/client.h>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <atomic>
#include <algorithm>
#include <sstream>
#include <memory>
#include <map>
#include <cstdint>

#pragma comment(lib, "d2d1.lib")
#pragma comment(lib, "dwrite.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdi32.lib")

using Microsoft::WRL::ComPtr;

namespace {
constexpr wchar_t kClassName[] = L"BITOS.Native.Direct2D.Window";
constexpr UINT WM_SERVER_MESSAGE = WM_APP + 41;
constexpr UINT WM_SERVER_EXIT = WM_APP + 42;
constexpr wchar_t kVersion[] = L"06V6";
constexpr wchar_t kBuild[] = L"21.01 BETA";

std::wstring Utf8ToWide(const std::string& value) {
    if (value.empty()) return {};
    int count = MultiByteToWideChar(CP_UTF8, 0, value.data(), (int)value.size(), nullptr, 0);
    if (count <= 0) return {};
    std::wstring result((size_t)count, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, value.data(), (int)value.size(), result.data(), count);
    return result;
}
std::string WideToUtf8(const std::wstring& value) {
    if (value.empty()) return {};
    int count = WideCharToMultiByte(CP_UTF8, 0, value.data(), (int)value.size(), nullptr, 0, nullptr, nullptr);
    if (count <= 0) return {};
    std::string result((size_t)count, '\0');
    WideCharToMultiByte(CP_UTF8, 0, value.data(), (int)value.size(), result.data(), count, nullptr, nullptr);
    return result;
}
std::string JsonEscape(const std::string& value) {
    std::string out; out.reserve(value.size() + 8);
    for (unsigned char c : value) {
        switch (c) {
        case '"': out += "\\\""; break;
        case '\\': out += "\\\\"; break;
        case '\n': out += "\\n"; break;
        case '\r': out += "\\r"; break;
        case '\t': out += "\\t"; break;
        default: if (c < 0x20) out += ' '; else out += (char)c;
        }
    }
    return out;
}
std::string JsonGetString(const std::string& json, const std::string& key) {
    const std::string needle = "\"" + key + "\":\"";
    size_t p = json.find(needle);
    if (p == std::string::npos) return {};
    p += needle.size();
    std::string out; bool esc = false;
    for (; p < json.size(); ++p) {
        char c = json[p];
        if (esc) {
            switch (c) {
            case 'n': out += '\n'; break; case 'r': out += '\r'; break; case 't': out += '\t'; break;
            case 'b': out += '\b'; break; case 'f': out += '\f'; break; default: out += c; break;
            }
            esc = false;
        } else if (c == '\\') esc = true;
        else if (c == '"') break;
        else out += c;
    }
    return out;
}
int JsonGetInt(const std::string& json, const std::string& key, int fallback = 0) {
    const std::string needle = "\"" + key + "\":";
    size_t p = json.find(needle); if (p == std::string::npos) return fallback;
    p += needle.size(); while (p < json.size() && (json[p] == ' ' || json[p] == '\t')) ++p;
    try { return std::stoi(json.substr(p)); } catch (...) { return fallback; }
}
bool JsonGetBool(const std::string& json, const std::string& key, bool fallback = false) {
    const std::string needle = "\"" + key + "\":";
    size_t p = json.find(needle); if (p == std::string::npos) return fallback;
    p += needle.size(); while (p < json.size() && json[p] == ' ') ++p;
    if (json.compare(p, 4, "true") == 0) return true;
    if (json.compare(p, 5, "false") == 0) return false;
    return fallback;
}
std::vector<std::wstring> JsonGetStringArray(const std::string& json, const std::string& arrayKey, const std::string& memberKey) {
    std::vector<std::wstring> values;
    const std::string startNeedle = "\"" + arrayKey + "\":";
    size_t start = json.find(startNeedle); if (start == std::string::npos) return values;
    size_t end = json.find(']', start); if (end == std::string::npos) return values;
    std::string part = json.substr(start, end - start);
    size_t pos = 0;
    const std::string memberNeedle = "\"" + memberKey + "\":\"";
    while ((pos = part.find(memberNeedle, pos)) != std::string::npos) {
        size_t valueStart = pos + memberNeedle.size();
        size_t i = valueStart; bool esc = false;
        for (; i < part.size(); ++i) {
            if (esc) esc = false;
            else if (part[i] == '\\') esc = true;
            else if (part[i] == '"') break;
        }
        if (i > valueStart && i <= part.size()) values.push_back(Utf8ToWide(part.substr(valueStart, i - valueStart)));
        pos = i + 1;
    }
    return values;
}

class BackendPipe {
public:
    BackendPipe() = default;
    ~BackendPipe() { Stop(); }
    bool Start(HWND window, const std::wstring& serverPath) {
        window_ = window;
        SECURITY_ATTRIBUTES sa{ sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE };
        HANDLE childStdinRead = nullptr, childStdoutWrite = nullptr;
        if (!CreatePipe(&childStdinRead, &stdinWrite_, &sa, 0)) return false;
        if (!SetHandleInformation(stdinWrite_, HANDLE_FLAG_INHERIT, 0)) return false;
        if (!CreatePipe(&stdoutRead_, &childStdoutWrite, &sa, 0)) return false;
        if (!SetHandleInformation(stdoutRead_, HANDLE_FLAG_INHERIT, 0)) return false;

        std::wstring command = L"\"python.exe\" \"" + serverPath + L"\"";
        STARTUPINFOW si{}; si.cb = sizeof(si); si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
        si.wShowWindow = SW_HIDE; si.hStdInput = childStdinRead; si.hStdOutput = childStdoutWrite; si.hStdError = childStdoutWrite;
        PROCESS_INFORMATION pi{};
        std::wstring cwd = serverPath.substr(0, serverPath.find_last_of(L"\\/"));
        BOOL created = CreateProcessW(nullptr, command.data(), nullptr, nullptr, TRUE, CREATE_NO_WINDOW,
                                      nullptr, cwd.empty() ? nullptr : cwd.c_str(), &si, &pi);
        CloseHandle(childStdinRead); CloseHandle(childStdoutWrite);
        if (!created) {
            Close();
            return false;
        }
        process_ = pi.hProcess; thread_ = pi.hThread;
        alive_ = true;
        reader_ = std::thread([this]() { ReadLoop(); });
        return true;
    }
    bool Send(const std::string& command, const std::string& fields = {}) {
        if (!alive_ || !stdinWrite_) return false;
        std::lock_guard<std::mutex> guard(writeMutex_);
        std::uint32_t id = ++nextId_;
        std::string line = "{\"id\":" + std::to_string(id) + ",\"command\":\"" + JsonEscape(command) + "\"";
        if (!fields.empty()) line += "," + fields;
        line += "}\n";
        DWORD written = 0;
        return WriteFile(stdinWrite_, line.data(), (DWORD)line.size(), &written, nullptr) && written == line.size();
    }
    void Stop() {
        if (stdinWrite_ && alive_) {
            Send("quit");
            FlushFileBuffers(stdinWrite_);
        }
        alive_ = false;
        if (stdinWrite_) { CloseHandle(stdinWrite_); stdinWrite_ = nullptr; }
        if (process_) {
            DWORD wait = WaitForSingleObject(process_, 1200);
            if (wait == WAIT_TIMEOUT) TerminateProcess(process_, 0);
        }
        if (stdoutRead_) { CancelIoEx(stdoutRead_, nullptr); CloseHandle(stdoutRead_); stdoutRead_ = nullptr; }
        if (reader_.joinable()) reader_.join();
        if (thread_) { CloseHandle(thread_); thread_ = nullptr; }
        if (process_) { CloseHandle(process_); process_ = nullptr; }
    }
    bool IsAlive() const { return alive_; }
private:
    void ReadLoop() {
        std::string pending;
        char buffer[4096];
        while (alive_ && stdoutRead_) {
            DWORD read = 0;
            BOOL ok = ReadFile(stdoutRead_, buffer, sizeof(buffer), &read, nullptr);
            if (!ok || read == 0) break;
            pending.append(buffer, buffer + read);
            size_t newline;
            while ((newline = pending.find('\n')) != std::string::npos) {
                std::string line = pending.substr(0, newline);
                pending.erase(0, newline + 1);
                auto* message = new std::wstring(Utf8ToWide(line));
                if (!PostMessageW(window_, WM_SERVER_MESSAGE, 0, (LPARAM)message)) delete message;
            }
        }
        alive_ = false;
        PostMessageW(window_, WM_SERVER_EXIT, 0, 0);
    }
    HWND window_ = nullptr;
    HANDLE process_ = nullptr, thread_ = nullptr, stdinWrite_ = nullptr, stdoutRead_ = nullptr;
    std::thread reader_;
    std::mutex writeMutex_;
    std::atomic<bool> alive_{ false };
    std::atomic<std::uint32_t> nextId_{ 0 };
};

enum class Screen { Splash, Login, Desktop, Settings };
struct DesktopItem { std::wstring name; };

class BITOSApp {
public:
    bool Initialize(HINSTANCE instance) {
        instance_ = instance;
        SetProcessDPIAware(); // Available on Windows 7; prevents blurry legacy scaling.
        if (FAILED(D2D1CreateFactory(D2D1_FACTORY_TYPE_SINGLE_THREADED, &d2dFactory_))) return false;
        if (FAILED(DWriteCreateFactory(DWRITE_FACTORY_TYPE_SHARED, __uuidof(IDWriteFactory), &dwriteFactory_))) return false;
        WNDCLASSEXW wc{}; wc.cbSize = sizeof(wc); wc.style = CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS;
        wc.lpfnWndProc = WindowProc; wc.hInstance = instance_; wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
        wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1); wc.lpszClassName = kClassName;
        RegisterClassExW(&wc);
        int sw = GetSystemMetrics(SM_CXSCREEN), sh = GetSystemMetrics(SM_CYSCREEN);
        hwnd_ = CreateWindowExW(WS_EX_APPWINDOW, kClassName, L"BITOS", WS_POPUP,
                                0, 0, sw, sh, nullptr, nullptr, instance_, this);
        if (!hwnd_) return false;
        ShowWindow(hwnd_, SW_SHOW); UpdateWindow(hwnd_);
        std::wstring module = ModuleDirectory() + L"\\BITOS_Server.py";
        if (!backend_.Start(hwnd_, module)) {
            screen_ = Screen::Login;
            status_ = L"Не удалось запустить BITOS_Server.py. Установите Python 3 и проверьте PATH.";
            InvalidateRect(hwnd_, nullptr, FALSE);
            return true;
        }
        backend_.Send("boot");
        SetTimer(hwnd_, 1, 1000, nullptr);
        return true;
    }
    int Run() {
        MSG msg{};
        while (GetMessageW(&msg, nullptr, 0, 0) > 0) { TranslateMessage(&msg); DispatchMessageW(&msg); }
        return (int)msg.wParam;
    }
    ~BITOSApp() { backend_.Stop(); DiscardDeviceResources(); }

    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam) {
        BITOSApp* self = reinterpret_cast<BITOSApp*>(GetWindowLongPtrW(hwnd, GWLP_USERDATA));
        if (message == WM_NCCREATE) {
            auto* create = reinterpret_cast<CREATESTRUCTW*>(lParam);
            self = static_cast<BITOSApp*>(create->lpCreateParams);
            SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(self));
        }
        if (!self) return DefWindowProcW(hwnd, message, wParam, lParam);
        return self->HandleMessage(message, wParam, lParam);
    }
private:
    static std::wstring ModuleDirectory() {
        wchar_t path[32768]{}; GetModuleFileNameW(nullptr, path, (DWORD)_countof(path));
        std::wstring value(path); size_t pos = value.find_last_of(L"\\/");
        return pos == std::wstring::npos ? L"." : value.substr(0, pos);
    }
    LRESULT HandleMessage(UINT message, WPARAM wParam, LPARAM lParam) {
        switch (message) {
        case WM_SIZE: Resize(); InvalidateRect(hwnd_, nullptr, FALSE); return 0;
        case WM_DISPLAYCHANGE: Resize(); InvalidateRect(hwnd_, nullptr, FALSE); return 0;
        case WM_ERASEBKGND: return 1;
        case WM_PAINT: { PAINTSTRUCT ps{}; BeginPaint(hwnd_, &ps); Render(); EndPaint(hwnd_, &ps); return 0; }
        case WM_TIMER:
            if (wParam == 1 && screen_ == Screen::Desktop) InvalidateRect(hwnd_, nullptr, FALSE);
            return 0;
        case WM_CHAR: HandleChar((wchar_t)wParam); return 0;
        case WM_KEYDOWN:
            if (wParam == VK_RETURN) { if (screen_ == Screen::Login) SubmitLogin(); }
            else if (wParam == VK_ESCAPE) { if (screen_ == Screen::Settings) screen_ = Screen::Desktop; else if (menuOpen_) menuOpen_ = false; }
            else if (wParam == VK_BACK) HandleBackspace();
            InvalidateRect(hwnd_, nullptr, FALSE); return 0;
        case WM_LBUTTONUP: HandleClick(GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam)); return 0;
        case WM_LBUTTONDBLCLK: HandleDoubleClick(GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam)); return 0;
        case WM_SERVER_MESSAGE: {
            std::unique_ptr<std::wstring> value(reinterpret_cast<std::wstring*>(lParam));
            if (value) HandleServerMessage(WideToUtf8(*value)); return 0;
        }
        case WM_SERVER_EXIT:
            if (screen_ != Screen::Login && screen_ != Screen::Desktop) status_ = L"Связь с сервером BITOS завершена.";
            else status_ = L"Потеряно соединение с сервером BITOS.";
            InvalidateRect(hwnd_, nullptr, FALSE); return 0;
        case WM_CLOSE:
            KillTimer(hwnd_, 1); backend_.Stop(); DestroyWindow(hwnd_); return 0;
        case WM_DESTROY: PostQuitMessage(0); return 0;
        }
        return DefWindowProcW(hwnd_, message, wParam, lParam);
    }
    void Resize() {
        if (!target_ || !hwnd_) return;
        RECT rc{}; GetClientRect(hwnd_, &rc);
        target_->Resize(D2D1::SizeU((UINT32)(rc.right - rc.left), (UINT32)(rc.bottom - rc.top)));
    }
    HRESULT CreateDeviceResources() {
        if (target_) return S_OK;
        RECT rc{}; GetClientRect(hwnd_, &rc);
        D2D1_SIZE_U size = D2D1::SizeU((UINT32)(rc.right - rc.left), (UINT32)(rc.bottom - rc.top));
        HRESULT hr = d2dFactory_->CreateHwndRenderTarget(D2D1::RenderTargetProperties(),
            D2D1::HwndRenderTargetProperties(hwnd_, size, D2D1_PRESENT_OPTIONS_NONE), &target_);
        if (SUCCEEDED(hr)) {
            hr = target_->CreateSolidColorBrush(D2D1::ColorF(0xFFFFFF), &sharedBrush_);
            textFormats_.clear();
        }
        return hr;
    }
    void DiscardDeviceResources() { target_.Reset(); sharedBrush_.Reset(); textFormats_.clear(); }
    void Fill(float l, float t, float r, float b, D2D1_COLOR_F color, float radius = 0) {
        if (!sharedBrush_) return;
        sharedBrush_->SetColor(color);
        D2D1_RECT_F rect = D2D1::RectF(l, t, r, b);
        if (radius > 0) target_->FillRoundedRectangle(D2D1::RoundedRect(rect, radius, radius), sharedBrush_.Get());
        else target_->FillRectangle(rect, sharedBrush_.Get());
    }
    void Stroke(float l, float t, float r, float b, D2D1_COLOR_F color, float width = 1.0f, float radius = 0) {
        if (!sharedBrush_) return;
        sharedBrush_->SetColor(color);
        D2D1_RECT_F rect = D2D1::RectF(l, t, r, b);
        if (radius > 0) target_->DrawRoundedRectangle(D2D1::RoundedRect(rect, radius, radius), sharedBrush_.Get(), width);
        else target_->DrawRectangle(rect, sharedBrush_.Get(), width);
    }
    void Line(float x1, float y1, float x2, float y2, D2D1_COLOR_F color, float width = 1) {
        if (!sharedBrush_) return;
        sharedBrush_->SetColor(color);
        target_->DrawLine(D2D1::Point2F(x1, y1), D2D1::Point2F(x2, y2), sharedBrush_.Get(), width);
    }
    void Text(const std::wstring& value, float l, float t, float r, float b, float size = 16,
              D2D1_COLOR_F color = D2D1::ColorF(0xFFFFFF), bool bold = false,
              DWRITE_TEXT_ALIGNMENT align = DWRITE_TEXT_ALIGNMENT_LEADING) {
        if (value.empty() || !sharedBrush_) return;
        const int cacheKey = (int)(size * 10.0f) * 2 + (bold ? 1 : 0);
        auto found = textFormats_.find(cacheKey);
        if (found == textFormats_.end()) {
            ComPtr<IDWriteTextFormat> fmt;
            if (FAILED(dwriteFactory_->CreateTextFormat(L"Segoe UI", nullptr, bold ? DWRITE_FONT_WEIGHT_SEMI_BOLD : DWRITE_FONT_WEIGHT_NORMAL,
                DWRITE_FONT_STYLE_NORMAL, DWRITE_FONT_STRETCH_NORMAL, size, L"ru-RU", &fmt))) return;
            found = textFormats_.emplace(cacheKey, fmt).first;
        }
        found->second->SetTextAlignment(align);
        found->second->SetParagraphAlignment(DWRITE_PARAGRAPH_ALIGNMENT_CENTER);
        sharedBrush_->SetColor(color);
        target_->DrawText(value.c_str(), (UINT32)value.size(), found->second.Get(), D2D1::RectF(l, t, r, b), sharedBrush_.Get(), D2D1_DRAW_TEXT_OPTIONS_CLIP);
    }
    void Button(const std::wstring& label, float l, float t, float r, float b, bool primary = false) {
        Fill(l, t, r, b, primary ? D2D1::ColorF(0x0078D4) : D2D1::ColorF(0x3A4B5B), 5);
        Text(label, l + 8, t, r - 8, b, 15, D2D1::ColorF(0xFFFFFF), true, DWRITE_TEXT_ALIGNMENT_CENTER);
    }
    void Render() {
        if (FAILED(CreateDeviceResources())) return;
        target_->BeginDraw();
        if (screen_ == Screen::Splash) DrawSplash();
        else if (screen_ == Screen::Login) DrawLogin();
        else if (screen_ == Screen::Desktop) DrawDesktop();
        else DrawSettings();
        HRESULT hr = target_->EndDraw();
        if (hr == D2DERR_RECREATE_TARGET) DiscardDeviceResources();
    }
    void DrawSplash() {
        Fill(0, 0, (float)width(), (float)height(), D2D1::ColorF(0x102235));
        Fill(0, height() * .64f, (float)width(), (float)height(), D2D1::ColorF(0x0B1825));
        Text(L"BITOS", 0, height() * .31f, (float)width(), height() * .46f, 62, D2D1::ColorF(0xEAF6FF), true, DWRITE_TEXT_ALIGNMENT_CENTER);
        Text(L"Операционная система", 0, height() * .46f, (float)width(), height() * .52f, 20, D2D1::ColorF(0x94B5CC), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        Text(L"Версия 06V6     •     Сборка 21.01 BETA", 0, height() * .56f, (float)width(), height() * .61f, 13, D2D1::ColorF(0xB7C9D7), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        float barW = std::min(420.0f, width() * .58f), x = (width() - barW) / 2;
        Fill(x, height() * .68f, x + barW, height() * .68f + 5, D2D1::ColorF(0x34485A), 3);
        Fill(x, height() * .68f, x + barW * bootProgress_ / 100.0f, height() * .68f + 5, D2D1::ColorF(0x2BA8E0), 3);
        Text(status_, x - 100, height() * .70f, x + barW + 100, height() * .76f, 14, D2D1::ColorF(0xD6E3ED), false, DWRITE_TEXT_ALIGNMENT_CENTER);
    }
    void DrawLogin() {
        Fill(0, 0, (float)width(), (float)height(), D2D1::ColorF(0x14283A));
        Fill(0, height() * .72f, (float)width(), (float)height(), D2D1::ColorF(0x102131));
        float cx = width() / 2.0f, cy = height() / 2.0f;
        Fill(cx - 225, cy - 245, cx + 225, cy + 245, D2D1::ColorF(0xF4F7FA), 12);
        Text(L"BITOS", cx - 190, cy - 220, cx + 190, cy - 158, 34, D2D1::ColorF(0x1D3447), true, DWRITE_TEXT_ALIGNMENT_CENTER);
        Text(L"Добро пожаловать", cx - 190, cy - 160, cx + 190, cy - 115, 19, D2D1::ColorF(0x52687A), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        Text(L"Имя пользователя", cx - 160, cy - 86, cx + 160, cy - 58, 13, D2D1::ColorF(0x34495B), true);
        Fill(cx - 160, cy - 56, cx + 160, cy - 9, D2D1::ColorF(0xFFFFFF), 4);
        Stroke(cx - 160, cy - 56, cx + 160, cy - 9, activeField_ == 0 ? D2D1::ColorF(0x0078D4) : D2D1::ColorF(0xC7D3DD), 1.5f, 4);
        Text(username_, cx - 148, cy - 56, cx + 148, cy - 9, 16, D2D1::ColorF(0x213547));
        Text(L"PIN-код", cx - 160, cy + 5, cx + 160, cy + 33, 13, D2D1::ColorF(0x34495B), true);
        Fill(cx - 160, cy + 35, cx + 160, cy + 82, D2D1::ColorF(0xFFFFFF), 4);
        Stroke(cx - 160, cy + 35, cx + 160, cy + 82, activeField_ == 1 ? D2D1::ColorF(0x0078D4) : D2D1::ColorF(0xC7D3DD), 1.5f, 4);
        Text(std::wstring(pin_.size(), L'•'), cx - 148, cy + 35, cx + 148, cy + 82, 18, D2D1::ColorF(0x213547));
        Button(L"Войти", cx - 160, cy + 104, cx + 160, cy + 153, true);
        Text(status_, cx - 190, cy + 162, cx + 190, cy + 207, 12, D2D1::ColorF(0xC43C3C), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        Text(L"По умолчанию PIN: 1234 (измените его после входа)", cx - 200, cy + 214, cx + 200, cy + 240, 10, D2D1::ColorF(0x8295A5), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        Text(L"Выключение", 24, height() - 58, 150, height() - 25, 13, D2D1::ColorF(0xE2EAF0));
    }
    void DrawDesktop() {
        Fill(0, 0, (float)width(), (float)height(), D2D1::ColorF(0x176A9E));
        // Calm Win10-era two-tone desktop backdrop.
        Fill(width() * .53f, 0, (float)width(), (float)height() - 48, D2D1::ColorF(0x125782));
        Text(L"BITOS", 30, 16, 220, 48, 25, D2D1::ColorF(0xFFFFFF), true);
        Text(L"Рабочий стол", 30, 47, 260, 72, 12, D2D1::ColorF(0xCFE6F3));
        const wchar_t* labels[] = { L"Этот компьютер", L"Проводник", L"Блокнот", L"Калькулятор", L"Терминал", L"Paint", L"Параметры" };
        const wchar_t* glyphs[] = { L"▣", L"📁", L"▤", L"＋", L">_", L"◩", L"⚙" };
        for (int i = 0; i < 7; ++i) {
            int col = i / 6, row = i % 6;
            float x = 28.0f + col * 112.0f, y = 92.0f + row * 102.0f;
            Fill(x + 20, y, x + 72, y + 50, D2D1::ColorF(i == 6 ? 0xDDECF5 : 0xD4EAF7, .92f), 9);
            Text(glyphs[i], x + 20, y, x + 72, y + 50, 24, D2D1::ColorF(0x1A4F72), true, DWRITE_TEXT_ALIGNMENT_CENTER);
            Text(labels[i], x - 8, y + 53, x + 100, y + 86, 11, D2D1::ColorF(0xFFFFFF), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        }
        // Display virtual desktop objects supplied by the service.
        for (size_t i = 0; i < desktopItems_.size() && i < 8; ++i) {
            float x = 280.0f + (float)(i % 2) * 190.0f, y = 92.0f + (float)(i / 2) * 82.0f;
            Fill(x, y, x + 166, y + 54, D2D1::ColorF(0x164B6A, .92f), 6);
            Text(desktopItems_[i].name, x + 8, y + 3, x + 158, y + 50, 12, D2D1::ColorF(0xFFFFFF), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        }
        // Taskbar.
        Fill(0, height() - 48, (float)width(), (float)height(), D2D1::ColorF(0x172A3A, .98f));
        Fill(0, height() - 48, 52, (float)height(), D2D1::ColorF(0x0078D4));
        Text(L"⊞", 0, height() - 48, 52, (float)height(), 25, D2D1::ColorF(0xFFFFFF), true, DWRITE_TEXT_ALIGNMENT_CENTER);
        Text(L"Поиск", 65, height() - 48, 220, (float)height(), 13, D2D1::ColorF(0xB9CBD8));
        Text(username_, 240, height() - 48, 390, (float)height(), 13, D2D1::ColorF(0xFFFFFF));
        SYSTEMTIME st{}; GetLocalTime(&st); wchar_t clock[64]{};
        swprintf_s(clock, L"%02d:%02d\n%02d.%02d.%04d", st.wHour, st.wMinute, st.wDay, st.wMonth, st.wYear);
        Text(clock, width() - 120, height() - 45, width() - 20, height() - 4, 11, D2D1::ColorF(0xFFFFFF), false, DWRITE_TEXT_ALIGNMENT_CENTER);
        if (menuOpen_) DrawStartMenu();
        if (!status_.empty()) {
            Fill(20, height() - 108, 560, height() - 62, D2D1::ColorF(0x142536, .96f), 5);
            Text(status_, 32, height() - 104, 548, height() - 66, 12, D2D1::ColorF(0xEAF4FA));
        }
    }
    void DrawStartMenu() {
        float top = height() - 438;
        Fill(0, top, 440, height() - 48, D2D1::ColorF(0x182C3D, .98f));
        Text(L"BITOS", 28, top + 16, 200, top + 55, 23, D2D1::ColorF(0xFFFFFF), true);
        Text(L"Проводник", 30, top + 80, 400, top + 126, 16, D2D1::ColorF(0xFFFFFF));
        Text(L"Настройки", 30, top + 134, 400, top + 180, 16, D2D1::ColorF(0xFFFFFF));
        Text(L"Калькулятор", 30, top + 188, 400, top + 234, 16, D2D1::ColorF(0xFFFFFF));
        Text(L"Завершение работы", 30, top + 242, 400, top + 288, 16, D2D1::ColorF(0xFFFFFF));
        Text(L"Перезагрузка", 30, top + 296, 400, top + 342, 16, D2D1::ColorF(0xFFFFFF));
    }
    void DrawSettings() {
        Fill(0, 0, (float)width(), (float)height(), D2D1::ColorF(0xE9EEF2));
        Fill(0, 0, 250, (float)height(), D2D1::ColorF(0x1C3448));
        Text(L"BITOS", 28, 22, 210, 68, 27, D2D1::ColorF(0xFFFFFF), true);
        Text(L"Параметры", 28, 78, 220, 116, 16, D2D1::ColorF(0xD4E4EF));
        Text(L"Система", 28, 146, 220, 186, 15, D2D1::ColorF(0xFFFFFF), true);
        Text(L"Производительность", 28, 188, 230, 228, 13, settingsTab_ == 0 ? D2D1::ColorF(0xFFFFFF) : D2D1::ColorF(0xBBD1E0), settingsTab_ == 0);
        Text(L"Обновление", 28, 232, 230, 270, 13, settingsTab_ == 1 ? D2D1::ColorF(0xFFFFFF) : D2D1::ColorF(0xBBD1E0), settingsTab_ == 1);
        Text(L"Учётная запись", 28, 276, 230, 314, 13, D2D1::ColorF(0xBBD1E0));
        Text(L"Главная", 28, height() - 70, 220, height() - 30, 14, D2D1::ColorF(0xFFFFFF));
        Fill(280, 36, width() - 34, height() - 36, D2D1::ColorF(0xFFFFFF), 10);
        if (settingsTab_ == 1) {
            Text(L"Центр обновления BITOS", 320, 68, width() - 80, 126, 27, D2D1::ColorF(0x20394D), true);
            Text(L"Проверка выполняется в отдельном потоке. Архив проверяется по CRC и SHA-256 перед установкой.",
                 320, 133, width() - 86, 188, 14, D2D1::ColorF(0x62798A));
            Text(L"Текущая версия: 06V6     •     Сборка: 21.01 BETA", 340, 220, width() - 100, 256, 15, D2D1::ColorF(0x263E51), true);
            Text(L"Последняя версия: " + updateVersion_, 340, 260, width() - 100, 294, 14, D2D1::ColorF(0x62798A));
            Text(updateNotes_, 340, 300, width() - 100, height() - 220, 12, D2D1::ColorF(0x62798A));
            Button(L"Проверить обновления", 340, height() - 180, 560, height() - 132, false);
            Button(L"Скачать", 575, height() - 180, 715, height() - 132, false);
            Button(L"Установить", 730, height() - 180, 870, height() - 132, true);
            Text(status_, 340, height() - 122, width() - 80, height() - 82, 12, D2D1::ColorF(0xB23A3A));
            Text(L"Назад к рабочему столу", 28, height() - 70, 220, height() - 30, 14, D2D1::ColorF(0xFFFFFF));
            return;
        }
        if (settingsTab_ == 2) {
            Text(L"Учётная запись", 320, 68, width() - 80, 126, 27, D2D1::ColorF(0x20394D), true);
            Text(L"Изменение PIN-кода. Действующие правила: от 4 до 8 цифр.", 320, 133, width() - 86, 188, 14, D2D1::ColorF(0x62798A));
            Text(L"Текущий PIN", 340, 226, 650, 258, 13, D2D1::ColorF(0x34495B), true);
            Fill(340, 258, 660, 304, D2D1::ColorF(0xFFFFFF), 4);
            Stroke(340, 258, 660, 304, activeField_ == 2 ? D2D1::ColorF(0x0078D4) : D2D1::ColorF(0xC7D3DD), 1.5f, 4);
            Text(std::wstring(oldPin_.size(), L'•'), 352, 258, 648, 304, 16, D2D1::ColorF(0x213547));
            Text(L"Новый PIN", 340, 328, 650, 360, 13, D2D1::ColorF(0x34495B), true);
            Fill(340, 360, 660, 406, D2D1::ColorF(0xFFFFFF), 4);
            Stroke(340, 360, 660, 406, activeField_ == 3 ? D2D1::ColorF(0x0078D4) : D2D1::ColorF(0xC7D3DD), 1.5f, 4);
            Text(std::wstring(newPin_.size(), L'•'), 352, 360, 648, 406, 16, D2D1::ColorF(0x213547));
            Button(L"Изменить PIN", 340, 438, 520, 486, true);
            Text(status_, 340, 500, width() - 90, 550, 13, D2D1::ColorF(0xB23A3A));
            Text(L"Назад к рабочему столу", 28, height() - 70, 220, height() - 30, 14, D2D1::ColorF(0xFFFFFF));
            return;
        }
        Text(L"Производительность BITOS", 320, 68, width() - 80, 126, 27, D2D1::ColorF(0x20394D), true);
        Text(L"Выберите профиль оптимизации. Настройка сохраняется в System\\Config\\system.cfg.",
             320, 133, width() - 86, 188, 14, D2D1::ColorF(0x62798A));
        const int levels[] = { 0, 25, 50, 75, 100 };
        const wchar_t* names[] = { L"Максимум", L"Лёгкий", L"Сбалансированный", L"Экономия", L"Максимальная экономия" };
        const wchar_t* details[] = {
            L"Полный набор визуальных возможностей. Фоновая активность не ограничивается профилем BITOS.",
            L"Сокращает лишние перерисовки, оставляя основную часть визуальных эффектов.",
            L"Ограничивает необязательные фоновые задачи и упрощает часть эффектов.",
            L"Убирает большинство анимаций и уменьшает частоту необязательных обновлений.",
            L"Минимум фоновой активности. Перерисовка выполняется по событиям, таймеры обновляются редко."
        };
        float left = 340, top = 230;
        for (int i = 0; i < 5; ++i) {
            float y = top + i * 57;
            Fill(left, y, left + 34, y + 34, selectedOptimization_ == levels[i] ? D2D1::ColorF(0x0078D4) : D2D1::ColorF(0xE4EAF0), 6);
            Text(selectedOptimization_ == levels[i] ? L"✓" : L"", left, y, left + 34, y + 34, 17, D2D1::ColorF(0xFFFFFF), true, DWRITE_TEXT_ALIGNMENT_CENTER);
            Text(std::to_wstring(levels[i]) + L"%  —  " + names[i], left + 48, y - 2, width() - 400, y + 35, 16, D2D1::ColorF(0x263E51), true);
        }
        Text(details[selectedOptimization_ / 25], left + 48, top + 292, width() - 400, top + 356, 13, D2D1::ColorF(0x657B8C));
        Text(L"Текущий выбор: " + std::to_wstring(selectedOptimization_) + L"%", left, top + 370, left + 330, top + 410, 17, D2D1::ColorF(0x233F55), true);
        Button(L"Сохранить профиль", left, height() - 124, left + 210, height() - 74, false);
        Button(L"Сохранить и перезагрузить ПК", left + 226, height() - 124, left + 535, height() - 74, true);
        Text(status_, left, height() - 66, width() - 70, height() - 34, 12, D2D1::ColorF(0xB23A3A));
        Text(L"Версия 06V6   •   Сборка 21.01 BETA", width() - 360, height() - 70, width() - 60, height() - 35, 11, D2D1::ColorF(0x8294A2), false, DWRITE_TEXT_ALIGNMENT_TRAILING);
    }
    float width() const { RECT r{}; GetClientRect(hwnd_, &r); return (float)(r.right - r.left); }
    float height() const { RECT r{}; GetClientRect(hwnd_, &r); return (float)(r.bottom - r.top); }
    void HandleChar(wchar_t ch) {
        if (screen_ == Screen::Login) {
            if (activeField_ == 0) { if (ch >= 32 && username_.size() < 32) username_.push_back(ch); }
            else if (activeField_ == 1) { if (ch >= L'0' && ch <= L'9' && pin_.size() < 8) pin_.push_back(ch); }
        } else if (screen_ == Screen::Settings && settingsTab_ == 2) {
            if (activeField_ == 2 && ch >= L'0' && ch <= L'9' && oldPin_.size() < 8) oldPin_.push_back(ch);
            else if (activeField_ == 3 && ch >= L'0' && ch <= L'9' && newPin_.size() < 8) newPin_.push_back(ch);
        }
        InvalidateRect(hwnd_, nullptr, FALSE);
    }
    void HandleBackspace() {
        if (screen_ == Screen::Login) {
            if (activeField_ == 0 && !username_.empty()) username_.pop_back();
            else if (activeField_ == 1 && !pin_.empty()) pin_.pop_back();
        } else if (screen_ == Screen::Settings && settingsTab_ == 2) {
            if (activeField_ == 2 && !oldPin_.empty()) oldPin_.pop_back();
            else if (activeField_ == 3 && !newPin_.empty()) newPin_.pop_back();
        }
        InvalidateRect(hwnd_, nullptr, FALSE);
    }
    void SubmitLogin() {
        if (username_.empty() || pin_.empty()) { status_ = L"Введите имя пользователя и PIN-код."; InvalidateRect(hwnd_, nullptr, FALSE); return; }
        status_ = L"Проверка данных…";
        std::string fields = "\"username\":\"" + JsonEscape(WideToUtf8(username_)) + "\",\"pin\":\"" + JsonEscape(WideToUtf8(pin_)) + "\"";
        if (!backend_.Send("login", fields)) status_ = L"Нет соединения с сервером BITOS.";
        InvalidateRect(hwnd_, nullptr, FALSE);
    }
    void HandleClick(int x, int y) {
        const float cx = width() / 2.0f, cy = height() / 2.0f;
        if (screen_ == Screen::Login) {
            if (x >= cx - 160 && x <= cx + 160 && y >= cy - 56 && y <= cy - 9) activeField_ = 0;
            else if (x >= cx - 160 && x <= cx + 160 && y >= cy + 35 && y <= cy + 82) activeField_ = 1;
            else if (x >= cx - 160 && x <= cx + 160 && y >= cy + 104 && y <= cy + 153) SubmitLogin();
            else if (y >= height() - 68 && x < 175) {
                if (MessageBoxW(hwnd_, L"Выключить компьютер?", L"BITOS", MB_YESNO | MB_ICONQUESTION) == IDYES) backend_.Send("shutdown");
            }
        } else if (screen_ == Screen::Desktop) {
            if (y >= height() - 48 && x <= 52) { menuOpen_ = !menuOpen_; }
            else if (menuOpen_ && y >= height() - 358) {
                if (y < height() - 312) backend_.Send("open_app", "\"app\":\"explorer\"");
                else if (y < height() - 258) { screen_ = Screen::Settings; menuOpen_ = false; backend_.Send("get_settings"); }
                else if (y < height() - 204) backend_.Send("open_app", "\"app\":\"calculator\"");
                else if (y < height() - 150) { if (MessageBoxW(hwnd_, L"Завершить работу компьютера?", L"BITOS", MB_YESNO | MB_ICONQUESTION) == IDYES) backend_.Send("shutdown"); }
                else if (y < height() - 96) { if (MessageBoxW(hwnd_, L"Перезагрузить компьютер?", L"BITOS", MB_YESNO | MB_ICONQUESTION) == IDYES) backend_.Send("save_and_reboot", "\"value\":" + std::to_string(selectedOptimization_)); }
                menuOpen_ = false;
            } else if (x >= 145 && x < 250 && y >= 92 && y < 178) {
                screen_ = Screen::Settings; settingsTab_ = 0; backend_.Send("get_settings");
            } else if (y >= 92 && y < 92 + 6 * 102 && x < 145) {
                int row = (int)((y - 92) / 102); if (row < 0) row = 0;
                switch (row) {
                case 0: backend_.Send("open_app", "\"app\":\"explorer\""); break;
                case 1: backend_.Send("open_app", "\"app\":\"explorer\""); break;
                case 2: backend_.Send("open_app", "\"app\":\"notepad\""); break;
                case 3: backend_.Send("open_app", "\"app\":\"calculator\""); break;
                case 4: backend_.Send("open_app", "\"app\":\"terminal\""); break;
                case 5: backend_.Send("open_app", "\"app\":\"paint\""); break;
                default: screen_ = Screen::Settings; backend_.Send("get_settings"); break;
                }
            } else if (y >= height() - 48 && x > 230 && x < 390) {
                backend_.Send("logout");
            } else if (x > width() - 170 && y >= height() - 48) {
                // Clock / notification area is intentionally inert.
            }
        } else if (screen_ == Screen::Settings) {
            if (x < 245 && y > height() - 80) { screen_ = Screen::Desktop; status_.clear(); }
            else if (x < 245 && y >= 182 && y <= 230) { settingsTab_ = 0; status_.clear(); }
            else if (x < 245 && y >= 230 && y <= 275) { settingsTab_ = 1; status_ = L"Проверка обновлений…"; backend_.Send("check_updates"); }
            else if (x < 245 && y >= 275 && y <= 320) { settingsTab_ = 2; status_.clear(); activeField_ = 2; }
            else if (settingsTab_ == 2) {
                if (x >= 340 && x <= 660 && y >= 258 && y <= 304) activeField_ = 2;
                else if (x >= 340 && x <= 660 && y >= 360 && y <= 406) activeField_ = 3;
                else if (x >= 340 && x <= 520 && y >= 438 && y <= 486) {
                    if (oldPin_.size() >= 4 && newPin_.size() >= 4) {
                        backend_.Send("set_pin", "\"old_pin\":\"" + JsonEscape(WideToUtf8(oldPin_)) + "\",\"new_pin\":\"" + JsonEscape(WideToUtf8(newPin_)) + "\"");
                        status_ = L"Сохранение нового PIN…";
                    } else status_ = L"Оба PIN-кода должны содержать минимум 4 цифры.";
                }
            }
            else if (settingsTab_ == 1) {
                if (y >= height() - 180 && y <= height() - 132) {
                    if (x >= 340 && x <= 560) { status_ = L"Проверка обновлений…"; backend_.Send("check_updates"); }
                    else if (x >= 575 && x <= 715) {
                        if (updateAvailable_) { status_ = L"Загрузка обновления…"; backend_.Send("download_update"); }
                        else status_ = L"Сначала проверьте наличие обновлений.";
                    } else if (x >= 730 && x <= 870) {
                        if (updateDownloaded_) {
                            if (MessageBoxW(hwnd_, L"Установить проверенное обновление BITOS? Приложение будет закрыто на время установки.", L"Обновление BITOS", MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2) == IDYES)
                                backend_.Send("apply_update");
                        } else status_ = L"Сначала скачайте и проверьте обновление.";
                    }
                }
            } else {
                float left = 340, top = 230;
                for (int i = 0; i < 5; ++i) {
                    float yy = top + i * 57;
                    if (x >= left - 4 && x <= width() - 70 && y >= yy - 8 && y <= yy + 42) {
                        selectedOptimization_ = i * 25; break;
                    }
                }
                if (y >= height() - 124 && y <= height() - 74) {
                    if (x >= left && x <= left + 210) {
                        backend_.Send("set_optimization", "\"value\":" + std::to_string(selectedOptimization_));
                    } else if (x >= left + 226 && x <= left + 535) {
                        std::wstring prompt = L"Сохранить профиль " + std::to_wstring(selectedOptimization_) + L"% и выполнить полную перезагрузку Windows?";
                        if (MessageBoxW(hwnd_, prompt.c_str(), L"Перезагрузка BITOS", MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2) == IDYES)
                            backend_.Send("save_and_reboot", "\"value\":" + std::to_string(selectedOptimization_));
                    }
                }
            }
        }
        InvalidateRect(hwnd_, nullptr, FALSE);
    }
    void HandleDoubleClick(int x, int y) {
        if (screen_ != Screen::Desktop) return;
        for (size_t i = 0; i < desktopItems_.size() && i < 8; ++i) {
            float left = 280.0f + (float)(i % 2) * 190.0f, top = 92.0f + (float)(i / 2) * 82.0f;
            if (x >= left && x <= left + 166 && y >= top && y <= top + 54) {
                backend_.Send("open_item", "\"name\":\"" + JsonEscape(WideToUtf8(desktopItems_[i].name)) + "\""); return;
            }
        }
    }
    void HandleServerMessage(const std::string& json) {
        std::string event = JsonGetString(json, "event");
        bool ok = JsonGetBool(json, "ok", false);
        if (event == "boot_progress") {
            bootProgress_ = std::max(0, std::min(100, JsonGetInt(json, "progress", bootProgress_)));
            status_ = Utf8ToWide(JsonGetString(json, "status"));
        } else if (event == "boot_complete") {
            bootProgress_ = 100; selectedOptimization_ = JsonGetInt(json, "optimization", 0);
            screen_ = Screen::Login; status_ = L"Введите имя пользователя и PIN-код.";
        } else if (event == "login_result") {
            if (ok) {
                username_ = Utf8ToWide(JsonGetString(json, "username")); pin_.clear(); screen_ = Screen::Desktop; status_.clear();
                backend_.Send("desktop_state");
                UINT interval = selectedOptimization_ == 100 ? 60000 : selectedOptimization_ == 75 ? 30000 : selectedOptimization_ == 50 ? 15000 : selectedOptimization_ == 25 ? 5000 : 1000;
                SetTimer(hwnd_, 1, interval, nullptr);
            } else { status_ = Utf8ToWide(JsonGetString(json, "error")); pin_.clear(); }
        } else if (event == "desktop_state") {
            desktopItems_.clear();
            for (auto& name : JsonGetStringArray(json, "items", "name")) desktopItems_.push_back({ name });
            selectedOptimization_ = JsonGetInt(json, "optimization", selectedOptimization_);
        } else if (event == "settings") {
            selectedOptimization_ = JsonGetInt(json, "optimization", selectedOptimization_);
        } else if (event == "update_check_complete") {
            updateAvailable_ = ok && JsonGetBool(json, "available", false);
            updateVersion_ = Utf8ToWide(JsonGetString(json, "version"));
            updateNotes_ = Utf8ToWide(JsonGetString(json, "notes"));
            if (updateNotes_.size() > 900) updateNotes_.resize(900);
            status_ = ok ? (updateAvailable_ ? L"Доступно обновление." : L"Установлена актуальная версия.") : L"Ошибка проверки: " + Utf8ToWide(JsonGetString(json, "error"));
        } else if (event == "update_download_complete") {
            updateDownloaded_ = ok;
            status_ = ok ? L"Архив скачан и проверен." : L"Ошибка загрузки: " + Utf8ToWide(JsonGetString(json, "error"));
        } else if (event == "update_install_ready") {
            status_ = ok ? Utf8ToWide(JsonGetString(json, "message")) : L"Ошибка установки: " + Utf8ToWide(JsonGetString(json, "error"));
            if (ok) PostMessageW(hwnd_, WM_CLOSE, 0, 0);
        } else if (event == "pin_changed") {
            if (ok) { oldPin_.clear(); newPin_.clear(); status_ = L"PIN-код успешно изменён."; }
            else status_ = Utf8ToWide(JsonGetString(json, "error"));
        } else if (event == "restart_failed") {
            status_ = Utf8ToWide(JsonGetString(json, "error"));
        } else if (event == "optimization_saved") {
            if (ok) {
                selectedOptimization_ = JsonGetInt(json, "optimization", selectedOptimization_);
                status_ = JsonGetBool(json, "reboot_requested", false) ? L"Профиль сохранён. Запускается перезагрузка…" : L"Профиль оптимизации сохранён.";
                UINT interval = selectedOptimization_ == 100 ? 60000 : selectedOptimization_ == 75 ? 30000 : selectedOptimization_ == 50 ? 15000 : selectedOptimization_ == 25 ? 5000 : 1000;
                SetTimer(hwnd_, 1, interval, nullptr);
            } else status_ = Utf8ToWide(JsonGetString(json, "error"));
        } else if (event == "update_download_progress") {
            status_ = L"Загрузка обновления: " + std::to_wstring(JsonGetInt(json, "progress")) + L"%";
        } else if (event == "logout") {
            screen_ = Screen::Login; username_ = L"User"; pin_.clear(); status_ = L"Сеанс завершён.";
        } else if (event == "app_launched") {
            status_ = L"Запущено приложение Windows.";
        } else if (event == "error") {
            status_ = Utf8ToWide(JsonGetString(json, "error"));
        }
        InvalidateRect(hwnd_, nullptr, FALSE);
    }

    HINSTANCE instance_ = nullptr;
    HWND hwnd_ = nullptr;
    ComPtr<ID2D1Factory> d2dFactory_;
    ComPtr<IDWriteFactory> dwriteFactory_;
    ComPtr<ID2D1HwndRenderTarget> target_;
    ComPtr<ID2D1SolidColorBrush> sharedBrush_;
    std::map<int, ComPtr<IDWriteTextFormat>> textFormats_;
    BackendPipe backend_;
    Screen screen_ = Screen::Splash;
    std::wstring username_ = L"User", pin_, oldPin_, newPin_, status_ = L"Запуск системных компонентов…";
    std::vector<DesktopItem> desktopItems_;
    int activeField_ = 0;
    int bootProgress_ = 0;
    int selectedOptimization_ = 0;
    int settingsTab_ = 0;
    bool updateAvailable_ = false;
    bool updateDownloaded_ = false;
    std::wstring updateVersion_, updateNotes_;
    bool menuOpen_ = false;
};
} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int) {
    BITOSApp app;
    if (!app.Initialize(instance)) {
        MessageBoxW(nullptr, L"Не удалось инициализировать Win32 / Direct2D интерфейс BITOS.", L"BITOS", MB_ICONERROR | MB_OK);
        return 1;
    }
    return app.Run();
}
