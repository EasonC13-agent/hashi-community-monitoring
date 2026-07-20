def format_bitcoin_version(subversion: str) -> str:
    version = subversion.strip("/")

    if ":" in version:
        version = version.split(":", 1)[1]

    return f"v{version}"