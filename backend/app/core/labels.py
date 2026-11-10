"""Plain-word labels for snake_case codes that end up in stored, human-read text."""


def resolution_label(code: str) -> str:
    """"activity_explained" -> "Activity explained". Mirrors the frontend's formatResolutionCode."""
    spaced = " ".join(code.replace("_", " ").split())
    return spaced[:1].upper() + spaced[1:].lower()
