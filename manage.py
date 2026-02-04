#!/usr/bin/env python
import os
import sys


def main():
    """
    Entry point for Django administrative tasks.
    Sets the default settings module and delegates to Django.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "news_app_project.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
