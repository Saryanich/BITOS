# BITOS 06V6 source layout

Run the application with Python on Windows:

```powershell
python .\06V6\main.pyw
```

The source is divided into ordered modules under `06V6/modules/`. They are loaded into one shared runtime namespace to preserve the legacy application's cross-class references while the monolith is split into maintainable files.

| Module | Responsibility / source area |
|---|---|
| `security_and_files.py` | Startup screens, login, security, trash and early file-management classes |
| `file_explorer_apps.py` | File explorer, gallery, paint and desktop icons |
| `desktop_shell.py` | Taskbar, developer mode, installers and desktop shell |
| `system_core_widgets.py` | BITOS core, input blocker, wallpaper, notifications and widgets |
| `diagnostics_audio.py` | Error manager, safe-call helpers and sound |
| `settings_recovery.py` | Settings and automatic recovery |
| `multi_monitor.py` | Multi-monitor support and monitor widgets |

`bitos_update_manager.py` remains a separate module at the repository root because the generated restart/install script and update package are rooted at the BITOS installation directory. The launcher deliberately sets the runtime file path to the repository root so existing `System/` data remains in its prior location.
