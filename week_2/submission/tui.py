from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.containers import Vertical, Horizontal
from textual import work

from agent import ResearchAgent

class ChatApp(App):
    """A full-screen terminal research agent TUI."""
    
    TITLE = "Perplexity Clone - Week 2 Project"
    CSS = """
    Screen {
        layout: vertical;
    }

    #main_area {
        height: 1fr;
        layout: horizontal;
    }

    #chat_panel {
        width: 2fr;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
    }

    #tool_panel {
        width: 1fr;
        height: 100%;
        border: solid $secondary;
        padding: 0 1;
    }

    Input {
        dock: bottom;
        height: 3;
    }

    #stream_display {
        dock: bottom;
        height: auto;
        padding: 0 1;
        color: $accent;
        display: none;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear display"),
        Binding("ctrl+k", "clear_history", "Clear history"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.agent = ResearchAgent()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main_area"):
            yield RichLog(id="chat_panel", wrap=True, markup=True, highlight=True)
            yield RichLog(id="tool_panel", wrap=True, markup=True, highlight=True)
        yield Static(id="stream_display")
        yield Input(placeholder="Type your research question and press Enter...")
        yield Footer()

    def on_mount(self) -> None:
        chat_log = self.query_one("#chat_panel", RichLog)
        chat_log.write("[bold green]Research Agent Started.[/bold green] Ctrl+Q to quit.\n")
        
        tool_log = self.query_one("#tool_panel", RichLog)
        tool_log.write("[bold yellow]Tool Activity Log[/bold yellow]\n")
        
        self.query_one(Input).focus()

    @work
    async def fetch_response(self, user_text: str) -> None:
        chat_log = self.query_one("#chat_panel", RichLog)
        tool_log = self.query_one("#tool_panel", RichLog)
        stream_display = self.query_one("#stream_display", Static)
        input_box = self.query_one(Input)
        
        # Disable input while waiting
        input_box.disabled = True
        
        # Initialize streaming display
        stream_display.update("")
        stream_display.set_styles("display: block;")
        
        current_stream_text = ""
        
        def status_update(msg: str):
            tool_log.write(f"[dim]{msg}[/dim]")
            
        def stream_update(chunk_text: str):
            nonlocal current_stream_text
            current_stream_text += chunk_text
            stream_display.update(current_stream_text)
            
        import time
        start_time = time.time()
            
        try:
            answer = await self.agent.get_response(user_text, status_update, stream_update)
            elapsed = time.time() - start_time
            stream_display.set_styles("display: none;")
            chat_log.write(f"[bold magenta][Agent][/bold magenta] [italic dim](generated in {elapsed:.1f}s)[/italic dim]\n{answer}\n")
        except Exception as e:
            stream_display.set_styles("display: none;")
            chat_log.write(f"[bold red]Error: {e}[/bold red]\n")
        finally:
            input_box.disabled = False
            input_box.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return

        event.input.clear()
        chat_log = self.query_one("#chat_panel", RichLog)
        chat_log.write(f"[bold cyan][You][/bold cyan]\n{user_text}\n")
        
        # Dispatch the async worker
        self.fetch_response(user_text)

    def action_clear_display(self) -> None:
        """Clear the visible chat log."""
        self.query_one("#chat_panel", RichLog).clear()
        self.query_one("#chat_panel", RichLog).write("[bold green]Display cleared.[/bold green]\n")

    def action_clear_history(self) -> None:
        """Clear history and display."""
        self.agent = ResearchAgent()
        self.query_one("#chat_panel", RichLog).clear()
        self.query_one("#tool_panel", RichLog).clear()
        self.query_one("#chat_panel", RichLog).write("[bold green]History reset.[/bold green]\n")

if __name__ == "__main__":
    app = ChatApp()
    app.run()
