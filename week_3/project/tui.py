from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.containers import Vertical, Horizontal
from textual import work
import time

from agent import Agent

class TUIAgent(App, Agent):
    """A full-screen terminal research agent TUI."""
    
    TITLE = "Research Desk"
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
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, session_id=None):
        App.__init__(self)
        Agent.__init__(self, session_id)
        self.stream_text = ""
        self.ui_ready = False

    def _emit(self, event_type: str, data: str):
        if not self.ui_ready: return
        try:
            if event_type == "status":
                self.call_from_thread(self.query_one("#tool_panel", RichLog).write, f"[dim]{data}[/dim]")
            elif event_type == "tool_start":
                self.call_from_thread(self.query_one("#tool_panel", RichLog).write, f"\\n[bold cyan]Calling tool:[/bold cyan] {data}")
            elif event_type == "stream":
                self.stream_text += data
                self.call_from_thread(self.query_one("#stream_display", Static).update, self.stream_text)
        except:
            pass

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main_area"):
            yield RichLog(id="chat_panel", wrap=True, markup=True, highlight=True)
            yield RichLog(id="tool_panel", wrap=True, markup=True, highlight=True)
        yield Static(id="stream_display")
        yield Input(placeholder="Type your research question and press Enter...")
        yield Footer()

    def on_mount(self) -> None:
        self.ui_ready = True
        chat_log = self.query_one("#chat_panel", RichLog)
        chat_log.write(f"[bold green]Research Desk Started.[/bold green] Session ID: {self.session_id}. Ctrl+Q to quit.\\n")
        
        tool_log = self.query_one("#tool_panel", RichLog)
        tool_log.write("[bold yellow]Tool Activity Log[/bold yellow]\\n")
        
        # Dump previous messages if resuming
        if len(self.messages) > 1: # >1 because [0] is system prompt
            chat_log.write(f"[dim]Resumed session with {len(self.messages)} turns...[/dim]\\n")
            
        self.query_one(Input).focus()

    @work
    async def fetch_response(self, user_text: str) -> None:
        chat_log = self.query_one("#chat_panel", RichLog)
        stream_display = self.query_one("#stream_display", Static)
        input_box = self.query_one(Input)
        
        # Disable input while waiting
        self.call_from_thread(setattr, input_box, "disabled", True)
        
        self.stream_text = ""
        self.call_from_thread(stream_display.update, "")
        self.call_from_thread(stream_display.set_styles, "display: block;")
        
        start_time = time.time()
            
        try:
            # chat() is inherited from Agent
            answer = await self.chat(user_text)
            elapsed = time.time() - start_time
            self.call_from_thread(stream_display.set_styles, "display: none;")
            self.call_from_thread(chat_log.write, f"[bold magenta][Agent][/bold magenta] [italic dim](generated in {elapsed:.1f}s)[/italic dim]\\n{answer}\\n")
        except Exception as e:
            self.call_from_thread(stream_display.set_styles, "display: none;")
            self.call_from_thread(chat_log.write, f"[bold red]Error: {e}[/bold red]\\n")
        finally:
            self.call_from_thread(setattr, input_box, "disabled", False)
            self.call_from_thread(input_box.focus)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return

        event.input.clear()
        chat_log = self.query_one("#chat_panel", RichLog)
        chat_log.write(f"[bold cyan][You][/bold cyan]\\n{user_text}\\n")
        
        self.fetch_response(user_text)

    def action_clear_display(self) -> None:
        """Clear the visible chat log."""
        self.query_one("#chat_panel", RichLog).clear()
        self.query_one("#chat_panel", RichLog).write("[bold green]Display cleared.[/bold green]\\n")

if __name__ == "__main__":
    app = TUIAgent()
    app.run()