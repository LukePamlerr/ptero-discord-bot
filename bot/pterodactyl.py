import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

class ServerState(Enum):
    """Server power states"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    RESTARTING = "restarting"

@dataclass
class ServerInfo:
    """Server information structure"""
    id: str
    name: str
    identifier: str
    description: str
    limits: Dict[str, Any]
    feature_limits: Dict[str, Any]
    state: ServerState
    allocation: Dict[str, Any]
    user: Dict[str, Any]
    nest: int
    egg: int
    docker_image: str

@dataclass
class UserInfo:
    """User information structure"""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    language: str
    root_admin: bool
    created_at: str

class PterodactylAPI:
    """Async Pterodactyl API client"""
    
    def __init__(self, panel_url: str, api_key: str):
        self.panel_url = panel_url.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.panel_url}/api/application"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Pterodactyl API"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 401:
                    raise Exception("Invalid API key")
                elif response.status == 403:
                    raise Exception("Insufficient permissions")
                elif response.status == 404:
                    raise Exception("Resource not found")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                
                return await response.json()
    
    async def test_connection(self) -> bool:
        """Test API connection and credentials"""
        try:
            await self._request("GET", "/users")
            return True
        except Exception:
            return False
    
    # Server Management Methods
    
    async def get_servers(self, include_relations: bool = False) -> List[ServerInfo]:
        """Get all servers"""
        params = {"include": "user,allocation,nest,egg"} if include_relations else {}
        response = await self._request("GET", "/servers", params=params)
        
        servers = []
        for server_data in response.get("data", []):
            attributes = server_data["attributes"]
            servers.append(ServerInfo(
                id=attributes["id"],
                name=attributes["name"],
                identifier=attributes["identifier"],
                description=attributes["description"],
                limits=attributes["limits"],
                feature_limits=attributes["feature_limits"],
                state=ServerState(attributes.get("state", "stopped")),
                allocation=attributes.get("allocation", {}),
                user=attributes.get("user", {}),
                nest=attributes.get("nest", 0),
                egg=attributes.get("egg", 0),
                docker_image=attributes.get("docker_image", "")
            ))
        
        return servers
    
    async def get_server(self, server_id: str) -> Optional[ServerInfo]:
        """Get specific server information"""
        try:
            response = await self._request("GET", f"/servers/{server_id}", params={
                "include": "user,allocation,nest,egg"
            })
            
            attributes = response["data"]["attributes"]
            return ServerInfo(
                id=attributes["id"],
                name=attributes["name"],
                identifier=attributes["identifier"],
                description=attributes["description"],
                limits=attributes["limits"],
                feature_limits=attributes["feature_limits"],
                state=ServerState(attributes.get("state", "stopped")),
                allocation=attributes.get("allocation", {}),
                user=attributes.get("user", {}),
                nest=attributes.get("nest", 0),
                egg=attributes.get("egg", 0),
                docker_image=attributes.get("docker_image", "")
            )
        except Exception:
            return None
    
    async def start_server(self, server_id: str) -> bool:
        """Start a server"""
        try:
            await self._request("POST", f"/servers/{server_id}/power")
            return True
        except Exception:
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop a server"""
        try:
            await self._request("POST", f"/servers/{server_id}/power", json={"signal": "stop"})
            return True
        except Exception:
            return False
    
    async def restart_server(self, server_id: str) -> bool:
        """Restart a server"""
        try:
            await self._request("POST", f"/servers/{server_id}/power", json={"signal": "restart"})
            return True
        except Exception:
            return False
    
    async def kill_server(self, server_id: str) -> bool:
        """Force kill a server"""
        try:
            await self._request("POST", f"/servers/{server_id}/power", json={"signal": "kill"})
            return True
        except Exception:
            return False
    
    async def send_command(self, server_id: str, command: str) -> bool:
        """Send command to server console"""
        try:
            await self._request("POST", f"/servers/{server_id}/command", json={"command": command})
            return True
        except Exception:
            return False
    
    async def get_server_resources(self, server_id: str) -> Dict[str, Any]:
        """Get server resource usage"""
        try:
            response = await self._request("GET", f"/servers/{server_id}/resources")
            return response.get("data", {}).get("attributes", {})
        except Exception:
            return {}
    
    # User Management Methods
    
    async def get_users(self) -> List[UserInfo]:
        """Get all users"""
        response = await self._request("GET", "/users")
        
        users = []
        for user_data in response.get("data", []):
            attributes = user_data["attributes"]
            users.append(UserInfo(
                id=attributes["id"],
                username=attributes["username"],
                email=attributes["email"],
                first_name=attributes["first_name"],
                last_name=attributes["last_name"],
                language=attributes["language"],
                root_admin=attributes["root_admin"],
                created_at=attributes["created_at"]
            ))
        
        return users
    
    async def get_user(self, user_id: str) -> Optional[UserInfo]:
        """Get specific user information"""
        try:
            response = await self._request("GET", f"/users/{user_id}")
            attributes = response["data"]["attributes"]
            return UserInfo(
                id=attributes["id"],
                username=attributes["username"],
                email=attributes["email"],
                first_name=attributes["first_name"],
                last_name=attributes["last_name"],
                language=attributes["language"],
                root_admin=attributes["root_admin"],
                created_at=attributes["created_at"]
            )
        except Exception:
            return None
    
    async def create_user(self, username: str, email: str, first_name: str, 
                         last_name: str, password: str) -> Optional[UserInfo]:
        """Create a new user"""
        try:
            response = await self._request("POST", "/users", json={
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "password": password
            })
            
            attributes = response["data"]["attributes"]
            return UserInfo(
                id=attributes["id"],
                username=attributes["username"],
                email=attributes["email"],
                first_name=attributes["first_name"],
                last_name=attributes["last_name"],
                language=attributes["language"],
                root_admin=attributes["root_admin"],
                created_at=attributes["created_at"]
            )
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user information"""
        try:
            await self._request("PATCH", f"/users/{user_id}", json=kwargs)
            return True
        except Exception:
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            await self._request("DELETE", f"/users/{user_id}")
            return True
        except Exception:
            return False
    
    # Node Management
    
    async def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes"""
        response = await self._request("GET", "/nodes")
        return [node["attributes"] for node in response.get("data", [])]
    
    # Nests and Eggs
    
    async def get_nests(self) -> List[Dict[str, Any]]:
        """Get all nests"""
        response = await self._request("GET", "/nests")
        return [nest["attributes"] for nest in response.get("data", [])]
    
    async def get_eggs(self, nest_id: int) -> List[Dict[str, Any]]:
        """Get eggs for a specific nest"""
        response = await self._request("GET", f"/nests/{nest_id}/eggs")
        return [egg["attributes"] for egg in response.get("data", [])]
