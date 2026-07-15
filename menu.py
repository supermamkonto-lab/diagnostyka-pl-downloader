#!/usr/bin/env python.exe
"""
Interactive TUI Menu for Medical Data Collector
Obsługuje: Install, Status, Konfiguracja, Uruchomienie
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.table import Table
except ImportError:
    print("⚠️  Brakuje 'rich'. Instaluję...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "-q"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.table import Table

console = Console()

REQUIREMENTS = {
    "playwright": "Playwright (Browser automation)",
    "pyyaml": "PyYAML (Config files)",
    "httpx": "HTTPX (HTTP client)",
    "rich": "Rich (Terminal UI)",
    "click": "Click (CLI framework)",
    "python-dateutil": "python-dateutil (Date utilities)",
}

PYTHON_PATH = sys.executable


def check_package(package_name: str) -> bool:
    """Sprawdź czy pakiet zainstalowany."""
    spec = importlib.util.find_spec(package_name.replace("-", "_"))
    return spec is not None


def install_requirements():
    """Zainstaluj wszystkie wymagane pakiety z progress barem."""
    console.clear()
    console.print(Panel("[bold cyan]📦 Instalacja Zależności[/bold cyan]", expand=False))

    missing = {name: desc for name, desc in REQUIREMENTS.items() if not check_package(name)}

    if not missing:
        console.print("[green]✓ Wszystkie pakiety już zainstalowane![/green]\n")
        return True

    console.print(f"\n[yellow]Brakuje {len(missing)} pakietów:[/yellow]\n")
    for name, desc in missing.items():
        console.print(f"  • {desc}")

    if not Confirm.ask("\n[bold]Zainstalować brakujące pakiety?[/bold]"):
        return False

    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Instalowanie...", total=len(missing))

        for package_name in missing.keys():
            progress.update(task, description=f"[cyan]Instalowanie {package_name}...")
            try:
                subprocess.check_call(
                    [PYTHON_PATH, "-m", "pip", "install", package_name, "-q"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                console.print(f"[red]✗ Błąd: nie udało się zainstalować {package_name}[/red]")
                return False
            progress.advance(task)

    console.print("[green]✓ Instalacja ukończona![/green]\n")
    return True


def install_playwright_browsers():
    """Zainstaluj Chromium dla Playwright."""
    console.clear()
    console.print(Panel("[bold cyan]🌐 Instalacja Chromium[/bold cyan]", expand=False))

    console.print("\n[yellow]Pobieranie Chromium (может zająć kilka minut)...[/yellow]\n")

    try:
        subprocess.check_call(
            [PYTHON_PATH, "-m", "playwright", "install", "chromium"],
            stdout=subprocess.DEVNULL,
        )
        console.print("[green]✓ Chromium zainstalowany![/green]\n")
        return True
    except subprocess.CalledProcessError:
        console.print("[red]✗ Błąd: nie udało się zainstalować Chromium[/red]\n")
        return False


def check_chrome_installed() -> bool:
    """Sprawdź czy Chrome zainstalowany na systemie."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    return any(Path(p).exists() for p in chrome_paths)


def show_status():
    """Pokaż status i statystykę."""
    console.clear()
    console.print(Panel("[bold cyan]📊 Status[/bold cyan]", expand=False))

    try:
        result = subprocess.run(
            [PYTHON_PATH, "run.py", "status"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(result.stdout)
        else:
            console.print("[red]Błąd: nie udało się pobrać statusu[/red]")
    except Exception as e:
        console.print(f"[red]Błąd: {e}[/red]")

    Prompt.ask("\n[dim]Wciśnij Enter aby wrócić[/dim]")


def edit_config():
    """Edycja konfiguracji."""
    config_path = Path("config/settings.yaml")

    if not config_path.exists():
        console.print(f"[red]Błąd: {config_path} nie istnieje[/red]")
        return

    console.clear()
    console.print(Panel("[bold cyan]⚙️  Edycja Konfiguracji[/bold cyan]", expand=False))
    console.print(f"\n[yellow]Ścieżka: {config_path.absolute()}[/yellow]\n")

    with open(config_path) as f:
        content = f.read()

    console.print(content)
    console.print("\n[dim]Otwórz plik w edytorze aby zmienić konfigurację[/dim]")

    if Confirm.ask("\nOtworzyć plik w Notatniku?"):
        os.startfile(str(config_path.absolute()))

    Prompt.ask("[dim]Wciśnij Enter aby wrócić[/dim]")


def run_collector():
    """Uruchom kolektor z wyborem opcji."""
    console.clear()
    console.print(Panel("[bold cyan]🚀 Uruchomienie Kolektora[/bold cyan]", expand=False))

    options = {
        "1": ("Ostatnie zlecenie (test)", "--limit=1"),
        "2": ("Ostatnie 5 zleceń", "--limit=5"),
        "3": ("Ostatnie 10 zleceń", "--limit=10"),
        "4": ("Wszystkie zlecenia", ""),
        "5": ("Powrót", None),
    }

    console.print("\n[bold]Wybierz co pobrać:[/bold]\n")
    for key, (desc, _) in options.items():
        console.print(f"  [{key}] {desc}")

    choice = Prompt.ask("\n[cyan]Twój wybór[/cyan]", choices=list(options.keys()), default="5")

    desc, limit_flag = options[choice]
    if limit_flag is None:
        return

    console.print(f"\n[bold cyan]► {desc}[/bold cyan]\n")
    console.print("[yellow]Chrome otworzy się za chwilę. Zaloguj się ręcznie do wyniki.diag.pl[/yellow]\n")

    cmd = [PYTHON_PATH, "run.py", "collect"]
    if limit_flag:
        cmd.append(limit_flag)

    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        console.print(f"[red]Błąd: {e}[/red]")

    Prompt.ask("\n[dim]Wciśnij Enter aby wrócić[/dim]")


def show_checklist():
    """Pokaż checklistę wymagań."""
    console.clear()
    console.print(Panel("[bold cyan]✓ Checklist Wymagań[/bold cyan]", expand=False))

    table = Table(title="Status Wymagań", show_header=True, header_style="bold cyan")
    table.add_column("Komponent", style="cyan")
    table.add_column("Status", style="green")

    # Python
    table.add_row("Python 3.13+", f"✓ {sys.version.split()[0]}")

    # Pakiety
    for package, desc in REQUIREMENTS.items():
        status = "✓" if check_package(package) else "✗"
        table.add_row(desc, status)

    # Chrome
    chrome_ok = check_chrome_installed()
    table.add_row("Google Chrome", "✓" if chrome_ok else "✗")

    # Chromium
    chromium_path = Path(os.path.expandvars(r"%USERPROFILE%\AppData\Local\ms-playwright\chromium-1228"))
    chromium_ok = chromium_path.exists()
    table.add_row("Playwright Chromium", "✓" if chromium_ok else "✗")

    console.print(table)

    missing = []
    if not all(check_package(p) for p in REQUIREMENTS.keys()):
        missing.append("Zainstaluj pakiety Python")
    if not chromium_ok:
        missing.append("Zainstaluj Playwright Chromium")
    if not chrome_ok:
        missing.append("Zainstaluj Google Chrome")

    if missing:
        console.print("\n[yellow]Brakuje:[/yellow]")
        for item in missing:
            console.print(f"  • {item}")
    else:
        console.print("\n[green]✓ Wszystko gotowe! Możesz uruchomić kolektor.[/green]")

    Prompt.ask("\n[dim]Wciśnij Enter aby wrócić[/dim]")


def main_menu():
    """Główne menu."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold cyan]Medical Data Collector[/bold cyan]\n[dim]Automatyczne pobieranie z wyniki.diag.pl[/dim]",
                expand=False,
            )
        )

        menu_options = {
            "1": ("🔧 Instalacja/Sprawdzenie", install_menu),
            "2": ("✓ Checklist Wymagań", show_checklist),
            "3": ("🚀 Uruchomienie", run_collector),
            "4": ("⚙️  Konfiguracja", edit_config),
            "5": ("📊 Status", show_status),
            "6": ("❌ Wyjście", None),
        }

        console.print("\n[bold]Menu:[/bold]\n")
        for key, (label, _) in menu_options.items():
            console.print(f"  [{key}] {label}")

        choice = Prompt.ask("\n[cyan]Twój wybór[/cyan]", choices=list(menu_options.keys()), default="6")

        if choice == "6":
            console.print("\n[cyan]Do widzenia![/cyan]\n")
            break

        label, func = menu_options[choice]
        if func:
            func()


def install_menu():
    """Menu instalacji."""
    while True:
        console.clear()
        console.print(Panel("[bold cyan]🔧 Instalacja[/bold cyan]", expand=False))

        options = {
            "1": ("Zainstaluj pakiety Python", install_requirements),
            "2": ("Zainstaluj Playwright Chromium", install_playwright_browsers),
            "3": ("Zainstaluj wszystko", install_all),
            "4": ("Powrót", None),
        }

        console.print("\n[bold]Wybierz:[/bold]\n")
        for key, (label, _) in options.items():
            console.print(f"  [{key}] {label}")

        choice = Prompt.ask("\n[cyan]Twój wybór[/cyan]", choices=list(options.keys()), default="4")

        if choice == "4":
            break

        label, func = options[choice]
        if func:
            func()


def install_all():
    """Zainstaluj wszystko."""
    if install_requirements():
        install_playwright_browsers()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Przerwano[/yellow]\n")
        sys.exit(0)
