from __future__ import annotations

from app.orchestrator.event_bus import event_bus


def cleanup_dead_letters(purge: bool = False) -> int:
	"""Return the number of dead-letter tasks, optionally clearing them."""
	dead_letters = event_bus.dead_letters()
	if purge and hasattr(event_bus, "clear_dead_letters"):
		try:
			event_bus.clear_dead_letters()
		except Exception:
			pass
	return len(dead_letters)