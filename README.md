# Drive Detective

Standalone, read-only C: drive analyzer for Windows.

## Download Windows EXE
1. Open [Windows builds](https://github.com/Becksploder2/Drive-Cleaner/actions/workflows/build.yml).
2. Choose the latest successful run.
3. Download `DriveDetective-Windows` under Artifacts.
4. Extract the ZIP and double-click `DriveDetective.exe`.

No Python or terminal is required on your computer.

## Features
- Scan C: for largest folders, sorted from largest to smallest.
- Stop a scan without changing files.
- Open selected folders in Explorer.
- Open Windows installed-apps settings to uninstall programs.

## Important safety information
This release is strictly **read-only**. It cannot delete files or uninstall apps itself.
Protected system directories are marked for Windows-managed cleanup rather than manual deletion.
Folder sizes include subfolders, so entries overlap and should not be summed. Inaccessible files may be undercounted.
