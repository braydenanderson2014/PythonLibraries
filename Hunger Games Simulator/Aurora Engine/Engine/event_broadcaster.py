"""
Enhanced Event Broadcasting System for Aurora Engine
Converts basic engine events into rich, dramatic narratives for the lobby server.
"""

import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class EventCategory(Enum):
    """Event categories for proper display prioritization"""
    DEATH = "death"              # Highest priority - tribute deaths
    COMBAT = "combat"            # Combat encounters, fights
    INJURY = "injury"            # Significant injuries
    ALLIANCE = "alliance"        # Alliance formations/betrayals
    SURVIVAL = "survival"        # Hunting, foraging, shelter
    EXPLORATION = "exploration"  # Discovery, travel
    SOCIAL = "social"            # Character moments, relationships
    ARENA_EVENT = "arena_event"  # Gamemaker interventions
    SPONSOR = "sponsor"          # Sponsor gifts
    PHASE = "phase"              # Phase transitions
    STATUS = "status"            # General status updates


class EventPriority(Enum):
    """Priority levels for event display"""
    CRITICAL = 5  # Deaths, game-changing events
    HIGH = 4      # Combat, injuries, alliances
    MEDIUM = 3    # Survival activities, discoveries
    LOW = 2       # Flavor events, minor activities
    MINIMAL = 1   # Status updates, transitions


class EventBroadcaster:
    """
    Enriches and broadcasts Aurora Engine events with dramatic narratives.
    Makes game output as engaging as the original simulator.
    """
    
    def __init__(self):
        self.event_history = []
        self.recent_narratives = []  # Track recent narratives to avoid repetition
        
        # Load dramatic descriptors
        self.combat_verbs = [
            "strikes", "lunges at", "attacks", "ambushes", "confronts",
            "charges", "assaults", "engages", "battles", "duels with"
        ]
        
        self.death_phrases = [
            "falls to", "is slain by", "succumbs to", "is killed by",
            "meets their end at the hands of", "is defeated by",
            "breathes their last after confronting", "dies fighting"
        ]
        
        self.survival_actions = [
            "scavenges for", "hunts", "searches for", "discovers",
            "finds", "secures", "gathers", "collects"
        ]
        
        self.emotional_states = {
            "fear": ["trembling", "terrified", "anxious", "nervous", "shaken"],
            "anger": ["furious", "enraged", "livid", "seething", "vengeful"],
            "determination": ["resolute", "focused", "determined", "driven", "unwavering"],
            "despair": ["hopeless", "desperate", "broken", "defeated", "lost"],
            "hope": ["optimistic", "hopeful", "encouraged", "inspired", "motivated"]
        }
        
    def broadcast_event(self, event: Dict[str, Any], game_state: Any) -> Dict[str, Any]:
        """
        Convert a basic Aurora Engine event into a rich, dramatic broadcast message.
        
        Args:
            event: Raw event from Aurora Engine
            game_state: Current game state for context
            
        Returns:
            Enhanced event message ready for server broadcast
        """
        event_type = event.get("message_type", "unknown")
        
        # Route to appropriate enhancement method
        if event_type == "game_event":
            return self._enhance_game_event(event, game_state)
        elif event_type == "tribute_death":
            return self._enhance_death_event(event, game_state)
        elif event_type == "phase_change":
            return self._enhance_phase_change(event, game_state)
        elif event_type == "cornucopia_bloodbath":
            return self._enhance_cornucopia_event(event, game_state)
        else:
            # Pass through with minimal enhancement
            return self._enhance_generic_event(event, game_state)
    
    def _enhance_game_event(self, event: Dict[str, Any], game_state: Any) -> Dict[str, Any]:
        """Enhance a standard game event with rich narrative"""
        data = event.get("data", {})
        event_data = data.get("event_data", {})
        event_type = data.get("event_type", "unknown")
        
        description = event_data.get("description", "Something happened")
        narrative = event_data.get("narrative", description)
        participants = event_data.get("participants", [])
        consequences = event_data.get("consequences", [])
        intensity = event_data.get("intensity", "medium")
        
        # Categorize the event
        category, priority = self._categorize_event(event_type, consequences)
        
        # Enrich the narrative
        enhanced_narrative = self._enrich_narrative(
            narrative, participants, consequences, intensity, game_state
        )
        
        # Create dramatic description
        enhanced_description = self._create_dramatic_description(
            description, participants, consequences, category, game_state
        )
        
        # Build broadcast message
        broadcast = {
            "message_type": "enhanced_game_event",
            "category": category.value,
            "priority": priority.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "title": enhanced_description,
                "narrative": enhanced_narrative,
                "participants": self._get_participant_details(participants, game_state),
                "consequences": self._format_consequences(consequences, game_state),
                "intensity": intensity,
                "original_event": event_type,
                "style_hints": self._get_display_hints(category, priority, intensity)
            }
        }
        
        # Store in history
        self.event_history.append(broadcast)
        self.recent_narratives.append(enhanced_narrative)
        if len(self.recent_narratives) > 10:
            self.recent_narratives.pop(0)
        
        return broadcast
    
    def _enhance_death_event(self, event: Dict[str, Any], game_state: Any) -> Dict[str, Any]:
        """Create dramatic death announcement"""
        data = event.get("data", {})
        victim_name = data.get("victim_name", "A tribute")
        victim_id = data.get("victim_id")
        killer_name = data.get("killer_name")
        cause = data.get("cause", "unknown circumstances")
        
        # Get victim details
        victim_district = "?"
        if victim_id and hasattr(game_state, 'tributes'):
            tribute = game_state.tributes.get(victim_id)
            if tribute and hasattr(tribute, 'district'):
                victim_district = tribute.district
        
        # Create dramatic death narrative
        if killer_name:
            death_verb = random.choice(self.death_phrases)
            narrative = f"💀 **{victim_name}** (District {victim_district}) {death_verb} **{killer_name}**."
            narrative += f"\n\n{self._generate_death_scene(victim_name, killer_name, cause, game_state)}"
        else:
            narrative = f"💀 **{victim_name}** (District {victim_district}) has died from {cause}."
            narrative += f"\n\n{self._generate_solo_death_scene(victim_name, cause, game_state)}"
        
        # Count remaining tributes
        alive_count = sum(1 for status in game_state.tribute_statuses.values() if status == "alive")
        narrative += f"\n\n**{alive_count} tributes remain.**"
        
        # Add cannon sound for dramatic effect
        cannon = "🔊 *BOOM!* A cannon fires in the distance."
        
        broadcast = {
            "message_type": "tribute_death",
            "category": EventCategory.DEATH.value,
            "priority": EventPriority.CRITICAL.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "title": f"💀 {victim_name} has fallen",
                "narrative": narrative,
                "cannon": cannon,
                "victim": {
                    "name": victim_name,
                    "id": victim_id,
                    "district": victim_district
                },
                "killer": killer_name,
                "tributes_remaining": alive_count,
                "style_hints": {
                    "sound_effect": "cannon",
                    "display_duration": 5000,  # Show for 5 seconds
                    "highlight_color": "#cc0000",
                    "importance": "critical"
                }
            }
        }
        
        self.event_history.append(broadcast)
        return broadcast
    
    def _enhance_phase_change(self, event: Dict[str, Any], game_state: Any) -> Dict[str, Any]:
        """Create atmospheric phase transition announcements"""
        data = event.get("data", {})
        phase_name = data.get("phase_name", "Unknown Phase")
        day = data.get("day", 1)
        time_of_day = data.get("time_of_day", "day")
        
        # Generate atmospheric description
        atmosphere = self._generate_phase_atmosphere(phase_name, time_of_day, day)
        
        # Count tributes
        alive_count = sum(1 for status in game_state.tribute_statuses.values() if status == "alive")
        
        title = f"🌅 {phase_name} - Day {day}"
        if time_of_day == "night":
            title = f"🌙 {phase_name} - Day {day}"
        
        narrative = f"{atmosphere}\n\n**{alive_count} tributes remain alive.**"
        
        broadcast = {
            "message_type": "phase_change",
            "category": EventCategory.PHASE.value,
            "priority": EventPriority.MEDIUM.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "title": title,
                "narrative": narrative,
                "phase": phase_name,
                "day": day,
                "time_of_day": time_of_day,
                "tributes_remaining": alive_count,
                "style_hints": {
                    "display_style": "banner",
                    "transition": "fade",
                    "duration": 3000
                }
            }
        }
        
        return broadcast
    
    def _enhance_cornucopia_event(self, event: Dict[str, Any], game_state: Any) -> Dict[str, Any]:
        """Create exciting cornucopia bloodbath narratives"""
        data = event.get("data", {})
        
        narrative = "⚔️ **THE CORNUCOPIA BLOODBATH**\n\n"
        narrative += "The gong sounds! Tributes sprint toward the Cornucopia, where weapons and supplies await. "
        narrative += "In the chaos, alliances form and break in seconds. Blood is spilled on the golden horn.\n\n"
        
        # Add dramatic details
        participants = data.get("participants", 0)
        deaths = data.get("deaths", 0)
        supplies = data.get("supplies_claimed", 0)
        
        narrative += f"**{participants} tributes** rush into the fray.\n"
        if deaths > 0:
            narrative += f"💀 **{deaths} tributes** fall in the initial bloodbath.\n"
        narrative += f"📦 **{supplies} supply caches** are claimed by survivors.\n"
        
        broadcast = {
            "message_type": "cornucopia_bloodbath",
            "category": EventCategory.ARENA_EVENT.value,
            "priority": EventPriority.CRITICAL.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "title": "⚔️ The Cornucopia Bloodbath",
                "narrative": narrative,
                "participants": participants,
                "casualties": deaths,
                "supplies": supplies,
                "style_hints": {
                    "display_style": "dramatic",
                    "sound_effect": "gong",
                    "importance": "critical",
                    "display_duration": 8000
                }
            }
        }
        
        return broadcast
    
    def _enhance_generic_event(self, event: Dict[str, Any], game_state: Any) -> Dict[str, Any]:
        """Minimal enhancement for unknown event types"""
        return {
            **event,
            "enhanced": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _enrich_narrative(self, narrative: str, participants: List[str],
                         consequences: List[Dict], intensity: str,
                         game_state: Any) -> str:
        """Add rich details to a narrative"""
        
        # If narrative is already detailed (> 100 chars), use it as-is
        if len(narrative) > 100:
            return narrative
        
        # Otherwise, expand it with context
        enhanced = narrative
        
        # Add participant details
        if participants and hasattr(game_state, 'tributes'):
            for participant_id in participants[:2]:  # Focus on first 2
                tribute = game_state.tributes.get(participant_id)
                if tribute:
                    # Add district info if not already present
                    if str(tribute.district) not in enhanced:
                        enhanced = enhanced.replace(
                            tribute.name,
                            f"{tribute.name} from District {tribute.district}",
                            1  # Only first occurrence
                        )
        
        # Add intensity-based flavor
        if intensity == "high" and len(enhanced) < 150:
            enhanced += " The stakes have never been higher."
        elif intensity == "critical" and len(enhanced) < 150:
            enhanced += " This moment will define the games."
        
        return enhanced
    
    def _create_dramatic_description(self, description: str, participants: List[str],
                                    consequences: List[Dict], category: EventCategory,
                                    game_state: Any) -> str:
        """Create a short, punchy description for the event"""
        
        # Check for deaths in consequences
        has_death = any(c.get("type") == "death" for c in consequences)
        
        if has_death and participants:
            victim_id = next((c.get("target") for c in consequences if c.get("type") == "death"), None)
            if victim_id and hasattr(game_state, 'tributes'):
                tribute = game_state.tributes.get(victim_id)
                if tribute:
                    return f"💀 {tribute.name} has been eliminated"
        
        # Use the existing description or create one
        if len(description) > 5:
            return description
        
        return "An event unfolds in the arena"
    
    def _categorize_event(self, event_type: str, consequences: List[Dict]) -> tuple:
        """Determine event category and priority"""
        
        # Check consequences for deaths
        has_death = any(c.get("type") == "death" for c in consequences)
        if has_death:
            return (EventCategory.DEATH, EventPriority.CRITICAL)
        
        # Check event type
        event_lower = event_type.lower()
        
        if "combat" in event_lower or "fight" in event_lower:
            return (EventCategory.COMBAT, EventPriority.HIGH)
        elif "injury" in event_lower or "wound" in event_lower:
            return (EventCategory.INJURY, EventPriority.HIGH)
        elif "alliance" in event_lower:
            return (EventCategory.ALLIANCE, EventPriority.HIGH)
        elif "hunt" in event_lower or "forage" in event_lower or "gather" in event_lower:
            return (EventCategory.SURVIVAL, EventPriority.MEDIUM)
        elif "explore" in event_lower or "discover" in event_lower:
            return (EventCategory.EXPLORATION, EventPriority.MEDIUM)
        elif "sponsor" in event_lower or "gift" in event_lower:
            return (EventCategory.SPONSOR, EventPriority.HIGH)
        elif "arena" in event_lower or "gamemaker" in event_lower:
            return (EventCategory.ARENA_EVENT, EventPriority.HIGH)
        else:
            return (EventCategory.SOCIAL, EventPriority.LOW)
    
    def _get_participant_details(self, participant_ids: List[str], game_state: Any) -> List[Dict]:
        """Get detailed information about event participants"""
        details = []
        
        if not hasattr(game_state, 'tributes'):
            return details
        
        for participant_id in participant_ids:
            tribute = game_state.tributes.get(participant_id)
            if tribute:
                details.append({
                    "id": participant_id,
                    "name": tribute.name if hasattr(tribute, 'name') else "Unknown",
                    "district": tribute.district if hasattr(tribute, 'district') else "?",
                    "health": tribute.health if hasattr(tribute, 'health') else 100,
                    "status": game_state.tribute_statuses.get(participant_id, "alive")
                })
        
        return details
    
    def _format_consequences(self, consequences: List[Dict], game_state: Any) -> List[str]:
        """Format consequences into readable strings"""
        formatted = []
        
        for consequence in consequences:
            cons_type = consequence.get("type", "unknown")
            target = consequence.get("target")
            
            if not target:
                continue
            
            # Get tribute name
            tribute_name = target
            if hasattr(game_state, 'tributes'):
                tribute = game_state.tributes.get(target)
                if tribute and hasattr(tribute, 'name'):
                    tribute_name = tribute.name
            
            if cons_type == "death":
                formatted.append(f"💀 {tribute_name} was killed")
            elif cons_type == "stat_effect":
                stat = consequence.get("stat", "stat")
                value = consequence.get("value", 0)
                direction = "increased" if value > 0 else "decreased"
                formatted.append(f"{tribute_name}'s {stat} {direction}")
            elif cons_type == "resource_add":
                resource = consequence.get("resource", "item")
                amount = consequence.get("amount", 1)
                formatted.append(f"{tribute_name} gained {amount} {resource}")
            elif cons_type == "injury":
                severity = consequence.get("severity", "minor")
                formatted.append(f"{tribute_name} suffered a {severity} injury")
        
        return formatted
    
    def _get_display_hints(self, category: EventCategory, priority: EventPriority, 
                          intensity: str) -> Dict[str, Any]:
        """Generate display hints for the UI"""
        hints = {
            "importance": priority.name.lower(),
            "urgency": intensity,
            "display_duration": 2000  # Default 2 seconds
        }
        
        # Adjust based on category
        if category == EventCategory.DEATH:
            hints["highlight_color"] = "#cc0000"
            hints["display_duration"] = 5000
            hints["sound_effect"] = "cannon"
        elif category == EventCategory.COMBAT:
            hints["highlight_color"] = "#ff6600"
            hints["display_duration"] = 3000
        elif category == EventCategory.ARENA_EVENT:
            hints["highlight_color"] = "#ffcc00"
            hints["display_duration"] = 4000
            hints["display_style"] = "dramatic"
        elif category == EventCategory.SPONSOR:
            hints["highlight_color"] = "#00cc66"
            hints["display_duration"] = 3000
            hints["icon"] = "gift"
        
        return hints
    
    def _generate_death_scene(self, victim: str, killer: str, cause: str, 
                             game_state: Any) -> str:
        """Generate a dramatic death scene description"""
        scenes = [
            f"In a brutal confrontation, {killer} gains the upper hand. {victim}'s desperate attempt to defend themselves fails, and they fall to the arena floor, never to rise again.",
            f"{killer} shows no mercy. Their attack is swift and decisive. {victim} barely has time to react before the fatal blow lands.",
            f"The fight is intense but brief. {killer}'s superior skill prevails, and {victim} realizes too late that this is their final moment.",
            f"With calculated precision, {killer} executes their strategy. {victim} fights valiantly but cannot overcome their opponent's determination.",
            f"{victim} and {killer} clash in a deadly dance. When the dust settles, only {killer} remains standing, their hands stained with blood."
        ]
        
        return random.choice(scenes)
    
    def _generate_solo_death_scene(self, victim: str, cause: str, game_state: Any) -> str:
        """Generate dramatic scene for non-combat deaths"""
        if "hunger" in cause.lower() or "starvation" in cause.lower():
            return f"{victim}'s body finally gives out after days without adequate food. They collapse, too weak to continue the fight for survival."
        elif "thirst" in cause.lower() or "dehydration" in cause.lower():
            return f"Unable to find water, {victim}'s strength fades. They succumb to dehydration, alone in the unforgiving arena."
        elif "exposure" in cause.lower() or "cold" in cause.lower():
            return f"The harsh elements prove too much. {victim} is found frozen, having lost their battle against the arena's cruel environment."
        elif "infection" in cause.lower() or "disease" in cause.lower():
            return f"A wound festers, and despite their best efforts, {victim} cannot fight off the infection. They pass quietly in the night."
        else:
            return f"The arena claims another victim. {victim}'s journey ends in tragedy, their death a reminder of the games' brutality."
    
    def _generate_phase_atmosphere(self, phase: str, time_of_day: str, day: int) -> str:
        """Generate atmospheric description for phase transitions"""
        if day == 1:
            return "The Games have begun. Twenty-four tributes entered the arena. How many will see tomorrow?"
        
        if time_of_day == "night":
            night_descriptions = [
                "Darkness falls over the arena. The nocturnal predators stir, and tributes huddle in their hiding places, wondering who the night will claim.",
                "The temperature drops as night descends. In the darkness, every sound is amplified, every shadow a potential threat.",
                "Another night in the arena begins. The fallen tributes' faces will appear in the sky, a grim reminder of the day's toll.",
                "The arena transforms under moonlight. What seems safe by day becomes treacherous after dark."
            ]
            return random.choice(night_descriptions)
        else:
            day_descriptions = [
                "Dawn breaks over the arena. The surviving tributes emerge from hiding, assessing what the new day will bring.",
                "Sunlight filters through the trees. Another day of survival begins, but for how many will it be their last?",
                "The arena awakens. Tributes must decide: hide and survive, or take risks for crucial supplies?",
                "Morning in the arena. The Gamemakers watch eagerly, ready to intervene if things become too quiet."
            ]
            return random.choice(day_descriptions)
