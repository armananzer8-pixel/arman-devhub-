import os
import sys

if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "mywebsite.settings"
    )

    from django.core.management import execute_from_command_line  # type: ignore[reportMissingModuleSource]
    execute_from_command_line(sys.argv)