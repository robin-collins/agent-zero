Below is a structured overview of how “workspaces” and Git/GitHub integration currently work in Agent-Zero—and where you might extend it to support per-project work folders and cloning.

1. Workspace (File System)
1.1 Base directory for file operations
- In production, the file browser roots at the system root (`/`).
  See `FileBrowser.__init__` setting
  [`python/helpers/file_browser.py:28-29`].
- In development, commented code would instead use the project base directory (`files.get_base_dir()`).
  Commented at [`python/helpers/file_browser.py:24-26`].

1.2 GetWorkDirFiles API handler
- Receives a `path` query (e.g. `$WORK_DIR` remapped to `"root"`).
  Mapping logic at
  [`python/api/get_work_dir_files.py:15-21`].
- Returns a directory listing via `FileBrowser.get_files`, invoked through
  `runtime.call_development_function` at
  [`python/api/get_work_dir_files.py:25-31`].

1.3 UploadWorkDirFiles API handler
- Upload endpoint for multipart file uploads into any subpath under the base directory.
  Entry point at
  [`python/api/upload_work_dir_files.py:17-23`], with helper
  `upload_files` at
  [`python/api/upload_work_dir_files.py:43-56`].

1.4 File utilities
- `files.get_base_dir()`: returns the project’s root folder
  [`python/helpers/files.py:325-328`].
- `files.get_abs_path(...)`: resolves relative paths against that base dir
  [`python/helpers/files.py:308-311`].

1.5 Commented Docker volume mapping
- In `initialize.py`, there is commented code that would mount
  a `work_dir` folder into `/root` inside a Docker container—signalling
  an intended “workspace” area.
  See commented block
  [`initialize.py:83-85`].

2. Settings and Configuration
2.1 Agent-specific subdirectories
- There are settings for prompts, memory and knowledge subfolders, but **no** setting for a general workspace path.
  - `agent_prompts_subdir`:
    [`python/helpers/settings.py:523-531`].
  - `agent_memory_subdir`:
    [`python/helpers/settings.py:537-542`].
  - `agent_knowledge_subdir`:
    [`python/helpers/settings.py:551-559`].

3. Git / GitHub Integration
3.1 Git metadata only
- The only built-in Git support is read-only inspection of the current repo via GitPython.
  - `get_git_info()` reads branch name, commit hash/time, and tags from `files.get_base_dir()`.
    Implementation starts at
    [`python/helpers/git.py:6-13`] and commit parsing at
    [`python/helpers/git.py:17-25`].

3.2 No clone/fetch/commit operations
- There is **no** endpoint or tool to `git clone`, push, or commit. To clone a GitHub repo you’d need to add a new tool (e.g. using `Repo.clone_from()` or shell commands via `helpers/shell_local.py`).

4. Summary & Next Steps
- Agent-Zero currently treats the **entire** file system (or project root in dev) as its workspace.
- File browsing and uploads go into that single root, with no isolated per-project workspace folder.
- Git support is limited to reading metadata from the codebase it’s running in.
- To support true per-project workspaces (e.g. cloning a repo or scaffolding a Python package), you would:
  1. Add a “workspace_path” setting in `settings.py` and expose it in `initialize_agent()`.
  2. Mount or create that folder in Docker (uncomment or extend the `code_exec_docker_volumes` block in [`initialize.py:83-85`]).
  3. Implement a new API/tool that performs `git clone` (using GitPython’s `Repo.clone_from()` or shell commands via `helpers/shell_local.py`) into that workspace.

With those changes in place, the agent could clone GitHub repos or generate packages in an isolated subdirectory, instead of working at `/` or the project root.

---

1. Workspace (File System)
- Base directory: `FileBrowser` defaults to `/` in production (`python/helpers/file_browser.py:28-29`) and would use the project root (`files.get_base_dir()`) in development (commented at `python/helpers/file_browser.py:24-26`).
- File listing: `GetWorkDirFiles` handles `GET /api/get_work_dir_files?path=…`, mapping `$WORK_DIR` to `"root"` (`python/api/get_work_dir_files.py:15-21`) and returning entries via `FileBrowser.get_files` (`python/api/get_work_dir_files.py:25-31`).
- File upload: `UploadWorkDirFiles` accepts multipart uploads into any subpath under the base directory (`python/api/upload_work_dir_files.py:17-23`), saving via `FileBrowser.save_files` (`python/api/upload_work_dir_files.py:43-56`).
- Path utilities: `files.get_base_dir()` returns the project root (`python/helpers/files.py:325-328`); `files.get_abs_path(...)` resolves relative paths against it (`python/helpers/files.py:308-311`).

2. Configuration
- No dedicated “workspace_path” setting exists. Agent-specific subdirectories only cover prompts (`agent_prompts_subdir`, `python/helpers/settings.py:523-531`), memory (`agent_memory_subdir`, `python/helpers/settings.py:537-542`), and knowledge (`agent_knowledge_subdir`, `python/helpers/settings.py:551-559`).

3. Git / GitHub
- Metadata only: `get_git_info()` reads branch, commit SHA, and tags from the current repo located at `files.get_base_dir()` (`python/helpers/git.py:6-13`, `python/helpers/git.py:17-25`).
- No clone/push/commit tools: There’s no endpoint or helper for `git clone`, `git push`, or branch operations. To support GitHub cloning, you would implement a new tool (e.g., using `Repo.clone_from()` from GitPython or shell via `helpers/shell_local.py`).

4. Extension Path
To enable per-project workspaces and Git operations:
- Add a new `workspace_path` setting in `settings.py` and expose it in `initialize_agent()` (`initialize.py`).
- In Docker configuration (commented in `initialize.py:83-85`), mount that path into the container.
- Create a new API/tool that performs repository cloning into `workspace_path` using GitPython’s `Repo.clone_from()` or shell commands via `python/helpers/shell_local.py`.