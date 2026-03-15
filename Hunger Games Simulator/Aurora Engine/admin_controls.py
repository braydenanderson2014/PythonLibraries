#!/usr/bin/env python3
"""
Aurora Engine Admin Controls
Provides admin-only endpoints for game management
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class AdminControls:
    """Manages admin commands for running game"""
    
    def __init__(self, aurora_integration, sio, lobby_manager):
        """
        Initialize admin controls
        
        Args:
            aurora_integration: AuroraLobbyIntegration instance
            sio: Socket.IO server instance  
            lobby_manager: LobbyManager instance
        """
        self.aurora_integration = aurora_integration
        self.sio = sio
        self.lobby_manager = lobby_manager
        
    async def force_next_event(self, lobby_id: str) -> Dict[str, Any]:
        """Force generation of next event immediately"""
        try:
            if lobby_id not in self.lobby_manager.lobbies:
                return {'success': False, 'error': 'Lobby not found'}
            
            lobby = self.lobby_manager.lobbies[lobby_id]
            if not hasattr(self.aurora_integration, 'engine') or not self.aurora_integration.engine:
                return {'success': False, 'error': 'Game engine not initialized'}
            
            # Generate event immediately
            event = self.aurora_integration.engine.generate_event()
            
            if event:
                # Broadcast event to all players
                await self.sio.emit('game_update', {
                    'lobby_id': lobby_id,
                    'message': event,
                    'timestamp': datetime.now().isoformat()
                }, room=lobby_id)
                
                return {
                    'success': True,
                    'event': event,
                    'message': f'Event forced: {event.get("message_type", "unknown")}'
                }
            else:
                return {'success': False, 'error': 'Failed to generate event'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def force_next_phase(self, lobby_id: str) -> Dict[str, Any]:
        """Force advance to next phase immediately"""
        try:
            if lobby_id not in self.lobby_manager.lobbies:
                return {'success': False, 'error': 'Lobby not found'}
            
            lobby = self.lobby_manager.lobbies[lobby_id]
            if not hasattr(self.aurora_integration, 'engine') or not self.aurora_integration.engine:
                return {'success': False, 'error': 'Game engine not initialized'}
            
            # Force phase advance by setting timer to now
            from datetime import datetime as dt
            self.aurora_integration.engine.game_state.phase_timer = dt.now()
            
            # Process tick to trigger phase advance
            messages = self.aurora_integration.process_game_tick()
            
            # Broadcast phase change
            if messages:
                for message in messages:
                    await self.sio.emit('game_update', {
                        'lobby_id': lobby_id,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    }, room=lobby_id)
            
            # Get new phase info
            phase_info = self.aurora_integration.engine.phase_controller.get_current_phase_info()
            
            return {
                'success': True,
                'new_phase': phase_info['phase_info']['name'] if phase_info else 'Unknown',
                'message': 'Phase advanced successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def update_config_timing(self, timing_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update engine configuration timing values
        
        Args:
            timing_updates: Dict with structure like:
            {
                'event_cooldowns': {'Combat Events': 30, ...},
                'phase_transitions': {'cornucopia': 30, ...}
            }
        """
        try:
            if not hasattr(self.aurora_integration, 'engine') or not self.aurora_integration.engine:
                return {'success': False, 'error': 'Game engine not initialized'}
            
            engine = self.aurora_integration.engine
            config = engine.config
            
            # Update timers
            if 'event_cooldowns' in timing_updates:
                if 'timers' not in config:
                    config['timers'] = {}
                config['timers']['event_cooldowns'] = timing_updates['event_cooldowns']
            
            if 'phase_transitions' in timing_updates:
                if 'timers' not in config:
                    config['timers'] = {}
                config['timers']['phase_transitions'] = timing_updates['phase_transitions']
            
            # Update game state timers
            engine.game_state.config = config
            
            return {
                'success': True,
                'message': 'Timing configuration updated',
                'updated_timings': timing_updates
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_tribute_stats(self, lobby_id: str, tribute_id: str = None) -> Dict[str, Any]:
        """Get current stats for a specific tribute or all tributes
        
        Args:
            lobby_id: ID of the lobby
            tribute_id: Optional - specific tribute ID, or None for all
        """
        try:
            if not hasattr(self.aurora_integration, 'engine') or not self.aurora_integration.engine:
                return {'success': False, 'error': 'Game engine not initialized'}
            
            scoreboards = self.aurora_integration.engine.game_state.get_tribute_scoreboards()
            
            if tribute_id:
                if tribute_id in scoreboards:
                    return {
                        'success': True,
                        'tribute': scoreboards[tribute_id]
                    }
                else:
                    return {'success': False, 'error': f'Tribute {tribute_id} not found'}
            else:
                return {
                    'success': True,
                    'tributes': scoreboards,
                    'count': len(scoreboards)
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def trigger_stat_decay(self, lobby_id: str) -> Dict[str, Any]:
        """Manually trigger stat decay for all tributes (simulates phase end)"""
        try:
            if not hasattr(self.aurora_integration, 'engine') or not self.aurora_integration.engine:
                return {'success': False, 'error': 'Game engine not initialized'}
            
            engine = self.aurora_integration.engine
            
            # Manually apply stat decay
            engine._apply_phase_end_stat_decay()
            
            # Get updated stats
            scoreboards = engine.game_state.get_tribute_scoreboards()
            
            # Broadcast update
            await self.sio.emit('engine_status_update', {
                'lobby_id': lobby_id,
                'tribute_scoreboards': scoreboards,
                'timestamp': datetime.now().isoformat()
            }, room=lobby_id)
            
            return {
                'success': True,
                'message': 'Stat decay applied to all tributes',
                'updated_tributes': len(scoreboards)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Usage in lobby_server.py:
# admin_controls = AdminControls(aurora_integration, sio, lobby_manager)
# Then add Socket.IO event handlers like:
# @sio.event
# async def admin_force_event(sid, data):
#     if not data.get('admin_key') == ADMIN_PASSWORD:
#         return {'error': 'Unauthorized'}
#     result = await admin_controls.force_next_event(data['lobby_id'])
#     await sio.emit('admin_response', result, room=sid)
