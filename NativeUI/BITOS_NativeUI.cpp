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
