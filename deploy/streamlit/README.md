# Hosted dashboard

The files here deploy the dashboard to
[Streamlit Community Cloud](https://streamlit.io/cloud), which hosts Streamlit apps
from a public GitHub repository for free.

| File | Purpose |
| :--- | :--- |
| `streamlit_app.py` | The entry point Community Cloud runs. It starts the dashboard shipped in the installed package. |
| `requirements.txt` | Exact dependency versions from `uv.lock`, plus `quant-core` itself installed from a release tag. Community Cloud reads the dependency file next to the entry point before any at the repository root. |

## Deploying

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub.
2. **Create app** → **Deploy a public app from GitHub**.
3. Repository `kyleyhw/quant_core`, branch `master`, main file path
   `deploy/streamlit/streamlit_app.py`.
4. Under **Advanced settings**, choose Python 3.12. Optionally set a custom
   subdomain.
5. **Deploy**.

## After a release

Point the last line of `requirements.txt` at the new tag and refresh the pinned
versions from the lockfile:

```bash
{ sed -n 1,3p deploy/streamlit/requirements.txt
  uv export --locked --no-dev --no-hashes --no-emit-project --no-header --format requirements-txt \
    | grep -v '^\s*#' | grep -v '^\s*$'
  echo "quant-core @ git+https://github.com/kyleyhw/quant_core@vX.Y.Z"
} > /tmp/requirements.txt && mv /tmp/requirements.txt deploy/streamlit/requirements.txt
```
