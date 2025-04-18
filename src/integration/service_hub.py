# src/integration/service_hub.py
"""
Service Hub module for the Egypt Tourism Chatbot.
Manages and orchestrates external service integrations.
"""
import json
import logging
import os
import requests
from typing import Dict, List, Any, Optional, Callable
import importlib
import inspect
from datetime import datetime, timedelta
from urllib.parse import urljoin
from pathlib import Path

logger = logging.getLogger(__name__)

class ServiceHub:
    """
    Service hub that manages external service integrations.
    Provides a unified interface for calling external services and APIs.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the service hub with configuration.
        
        Args:
            config_path (str): Path to service configuration file
        """
        self.config_path = config_path
        
        # Load service configurations
        self.config = self._load_config(config_path)
        
        # Initialize service instances
        self.services = {}
        self._initialize_services()
        
        # Initialize service plugins from the plugins directory
        self.plugins = {}
        self._load_plugins()
        
        logger.info("Service hub initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load service configurations from file."""
        try:
            # Check if file exists
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
                # Create default config if file doesn't exist
                default_config = self._create_default_config()
                
                # Save default config to file
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                
                return default_config
        except Exception as e:
            logger.error(f"Failed to load service configurations: {str(e)}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default service configurations."""
        return {
            "weather": {
                "type": "api",
                "base_url": "https://api.example.com/weather/",
                "api_key": "REPLACE_WITH_ACTUAL_API_KEY",
                "cache_ttl": 3600,  # 1 hour in seconds
                "endpoints": {
                    "forecast": {
                        "method": "GET",
                        "path": "forecast",
                        "params": ["city", "days"],
                        "required": ["city"]
                    },
                    "current": {
                        "method": "GET",
                        "path": "current",
                        "params": ["city"],
                        "required": ["city"]
                    }
                }
            },
            "translation": {
                "type": "plugin",
                "plugin_name": "translation_service",
                "config": {
                    "api_key": "REPLACE_WITH_ACTUAL_API_KEY",
                    "cache_ttl": 86400  # 24 hours in seconds
                }
            },
            "itinerary": {
                "type": "builtin",
                "methods": ["generate", "modify"],
                "config": {
                    "max_days": 14,
                    "cache_ttl": 3600  # 1 hour in seconds
                }
            },
            "geo": {
                "type": "api",
                "base_url": "https://api.example.com/geo/",
                "api_key": "REPLACE_WITH_ACTUAL_API_KEY",
                "cache_ttl": 604800,  # 7 days in seconds
                "endpoints": {
                    "geocode": {
                        "method": "GET",
                        "path": "geocode",
                        "params": ["address"],
                        "required": ["address"]
                    },
                    "nearby": {
                        "method": "GET",
                        "path": "nearby",
                        "params": ["lat", "lng", "type", "radius"],
                        "required": ["lat", "lng"]
                    }
                }
            }
        }
    
    def _initialize_services(self):
        """Initialize service instances based on configuration."""
        for service_name, service_config in self.config.items():
            try:
                service_type = service_config.get("type", "")
                
                if service_type == "api":
                    # Initialize REST API service
                    self.services[service_name] = APIService(
                        name=service_name,
                        config=service_config
                    )
                    logger.info(f"Initialized API service: {service_name}")
                
                elif service_type == "builtin":
                    # Initialize built-in service
                    self.services[service_name] = self._create_builtin_service(
                        name=service_name,
                        config=service_config
                    )
                    logger.info(f"Initialized built-in service: {service_name}")
                
                elif service_type == "plugin":
                    # Plugin services are loaded separately
                    pass
                
                else:
                    logger.warning(f"Unknown service type: {service_type} for {service_name}")
            
            except Exception as e:
                logger.error(f"Failed to initialize service {service_name}: {str(e)}")
    
    def _create_builtin_service(self, name: str, config: Dict) -> 'BuiltinService':
        """Create a built-in service instance."""
        if name == "itinerary":
            return ItineraryService(name=name, config=config)
        
        # Add more built-in services as needed
        
        # Default fallback
        return BuiltinService(name=name, config=config)
    
    def _load_plugins(self):
        """Load service plugins from the plugins directory."""
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        
        # Create plugins directory if it doesn't exist
        os.makedirs(plugins_dir, exist_ok=True)
        
        # Find all plugin services in configuration
        plugin_services = {
            name: config
            for name, config in self.config.items()
            if config.get("type") == "plugin"
        }
        
        for service_name, service_config in plugin_services.items():
            try:
                plugin_name = service_config.get("plugin_name", service_name)
                plugin_module_name = f"integration.plugins.{plugin_name}"
                
                # Try to import plugin module
                try:
                    plugin_module = importlib.import_module(plugin_module_name)
                    
                    # Find service class in module
                    service_class = None
                    for name, obj in inspect.getmembers(plugin_module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Service) and 
                            obj != Service and
                            obj.__module__ == plugin_module_name):
                            service_class = obj
                            break
                    
                    if service_class:
                        # Initialize service
                        self.services[service_name] = service_class(
                            name=service_name,
                            config=service_config.get("config", {})
                        )
                        logger.info(f"Loaded plugin service: {service_name}")
                    else:
                        logger.warning(f"No service class found in plugin: {plugin_name}")
                
                except ImportError as e:
                    logger.warning(f"Could not import plugin {plugin_name}: {str(e)}")
            
            except Exception as e:
                logger.error(f"Failed to load plugin service {service_name}: {str(e)}")
    
    def execute_service(self, service: str, method: str, params: Dict = None) -> Dict:
        """
        Execute a service method with parameters.
        
        Args:
            service (str): Service name
            method (str): Method name
            params (dict, optional): Method parameters
            
        Returns:
            dict: Service execution result
        """
        # Default empty params if None
        if params is None:
            params = {}
        
        # Check if service exists
        if service not in self.services:
            logger.error(f"Service not found: {service}")
            return {"error": f"Service not found: {service}"}
        
        # Execute service method
        try:
            service_instance = self.services[service]
            return service_instance.execute(method, params)
        except Exception as e:
            logger.error(f"Error executing service {service}.{method}: {str(e)}")
            return {"error": str(e)}
    
    def get_service(self, service: str) -> Optional['Service']:
        """
        Get a service instance by name.
        
        Args:
            service (str): Service name
            
        Returns:
            Service: Service instance if found, None otherwise
        """
        return self.services.get(service)
    
    def get_available_services(self) -> List[Dict]:
        """
        Get a list of available services and their methods.
        
        Returns:
            list: List of service information dictionaries
        """
        services = []
        
        for name, service in self.services.items():
            services.append({
                "name": name,
                "type": service.get_type(),
                "methods": service.get_methods()
            })
        
        return services


class Service:
    """Base class for service implementations."""
    
    def __init__(self, name: str, config: Dict):
        """
        Initialize a service.
        
        Args:
            name (str): Service name
            config (dict): Service configuration
        """
        self.name = name
        self.config = config
        self.cache = {}
        self.cache_ttl = config.get("cache_ttl", 3600)  # Default 1 hour
    
    def execute(self, method: str, params: Dict) -> Dict:
        """
        Execute a service method.
        
        Args:
            method (str): Method name
            params (dict): Method parameters
            
        Returns:
            dict: Execution result
        """
        # Check if method exists
        if not hasattr(self, method) or not callable(getattr(self, method)):
            return {"error": f"Method not found: {method}"}
        
        # Check cache
        cache_key = self._get_cache_key(method, params)
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() < cache_entry["expires"]:
                return cache_entry["result"]
        
        # Execute method
        try:
            result = getattr(self, method)(**params)
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
        except Exception as e:
            logger.error(f"Error in service {self.name}.{method}: {str(e)}")
            return {"error": str(e)}
    
    def _get_cache_key(self, method: str, params: Dict) -> str:
        """Generate a cache key for a method call."""
        # Sort params to ensure consistent keys
        sorted_params = sorted(params.items())
        params_str = json.dumps(sorted_params)
        
        return f"{self.name}:{method}:{params_str}"
    
    def _cache_result(self, key: str, result: Dict) -> None:
        """Cache a method result."""
        expires = datetime.now() + timedelta(seconds=self.cache_ttl)
        self.cache[key] = {
            "result": result,
            "expires": expires
        }
    
    def get_type(self) -> str:
        """Get the service type."""
        return "base"
    
    def get_methods(self) -> List[str]:
        """Get a list of available methods."""
        # Get all public methods (not starting with underscore)
        methods = []
        for name in dir(self):
            if not name.startswith('_') and callable(getattr(self, name)):
                # Exclude methods inherited from Service class
                if name not in dir(Service) or name == "execute":
                    methods.append(name)
        
        return methods


class APIService(Service):
    """Service implementation for REST APIs."""
    
    def __init__(self, name: str, config: Dict):
        """
        Initialize an API service.
        
        Args:
            name (str): Service name
            config (dict): Service configuration
        """
        super().__init__(name, config)
        self.base_url = config.get("base_url", "")
        self.api_key = config.get("api_key", "")
        self.endpoints = config.get("endpoints", {})
        
        # Initialize session
        self.session = requests.Session()
        
        # Add common headers if specified
        if "headers" in config:
            self.session.headers.update(config["headers"])
    
    def execute(self, method: str, params: Dict) -> Dict:
        """
        Execute an API endpoint.
        
        Args:
            method (str): Endpoint name
            params (dict): Request parameters
            
        Returns:
            dict: API response
        """
        # Check if endpoint exists
        if method not in self.endpoints:
            return {"error": f"Endpoint not found: {method}"}
        
        # Get endpoint configuration
        endpoint = self.endpoints[method]
        endpoint_method = endpoint.get("method", "GET")
        endpoint_path = endpoint.get("path", "")
        endpoint_params = endpoint.get("params", [])
        required_params = endpoint.get("required", [])
        
        # Check required parameters
        for param in required_params:
            if param not in params:
                return {"error": f"Missing required parameter: {param}"}
        
        # Check cache
        cache_key = self._get_cache_key(method, params)
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() < cache_entry["expires"]:
                return cache_entry["result"]
        
        # Prepare request
        url = urljoin(self.base_url, endpoint_path)
        
        # Filter parameters to include only those defined in endpoint
        request_params = {k: v for k, v in params.items() if k in endpoint_params}
        
        # Add API key if specified
        if self.api_key:
            request_params["api_key"] = self.api_key
        
        # Execute request
        try:
            if endpoint_method == "GET":
                response = self.session.get(url, params=request_params)
            elif endpoint_method == "POST":
                response = self.session.post(url, json=request_params)
            elif endpoint_method == "PUT":
                response = self.session.put(url, json=request_params)
            elif endpoint_method == "DELETE":
                response = self.session.delete(url, params=request_params)
            else:
                return {"error": f"Unsupported HTTP method: {endpoint_method}"}
            
            # Parse response
            response.raise_for_status()
            result = response.json()
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return {"error": f"API request error: {str(e)}"}
    
    def get_type(self) -> str:
        """Get the service type."""
        return "api"


class BuiltinService(Service):
    """Base class for built-in services."""
    
    def get_type(self) -> str:
        """Get the service type."""
        return "builtin"


class ItineraryService(BuiltinService):
    """Built-in service for itinerary generation and management."""
    
    def __init__(self, name: str, config: Dict):
        """
        Initialize the itinerary service.
        
        Args:
            name (str): Service name
            config (dict): Service configuration
        """
        super().__init__(name, config)
        self.max_days = config.get("max_days", 14)
    
    def generate(self, location: str, duration: Any, interests: List[str] = None) -> Dict:
        """
        Generate an itinerary for a location.
        
        Args:
            location (str): Destination location
            duration (int/str): Trip duration in days
            interests (list, optional): User interests
            
        Returns:
            dict: Generated itinerary
        """
        # Convert duration to integer
        try:
            if isinstance(duration, str):
                # Extract first number from string
                import re
                match = re.search(r'\d+', duration)
                if match:
                    days = int(match.group())
                else:
                    days = 3  # Default
            else:
                days = int(duration)
        except (ValueError, TypeError):
            days = 3  # Default to 3 days
        
        # Limit to max days
        days = min(days, self.max_days)
        
        # Default empty interests
        if interests is None:
            interests = []
        
        # Generate simple itinerary
        itinerary = self._generate_simple_itinerary(location, days, interests)
        
        return {
            "location": location,
            "duration": days,
            "interests": interests,
            "itinerary": itinerary
        }
    
    def modify(self, itinerary: Dict, changes: Dict) -> Dict:
        """
        Modify an existing itinerary.
        
        Args:
            itinerary (dict): Existing itinerary
            changes (dict): Requested changes
            
        Returns:
            dict: Modified itinerary
        """
        # Apply changes to itinerary
        if "location" in changes:
            itinerary["location"] = changes["location"]
        
        if "duration" in changes:
            try:
                days = int(changes["duration"])
                days = min(days, self.max_days)
                itinerary["duration"] = days
            except (ValueError, TypeError):
                pass
        
        if "interests" in changes:
            itinerary["interests"] = changes["interests"]
        
        # Re-generate itinerary content
        itinerary["itinerary"] = self._generate_simple_itinerary(
            itinerary["location"],
            itinerary["duration"],
            itinerary["interests"]
        )
        
        return itinerary
    
    def _generate_simple_itinerary(self, location: str, days: int, interests: List[str]) -> str:
        """Generate a simple text itinerary based on location and duration."""
        # This is a simplified placeholder implementation
        # In a real implementation, this would access the knowledge base
        # to get actual attractions, restaurants, etc.
        
        itinerary_text = f"Itinerary for {days} days in {location}\n\n"
        
        for day in range(1, days + 1):
            itinerary_text += f"Day {day}:\n"
            itinerary_text += f"- Morning: Visit a local attraction\n"
            itinerary_text += f"- Noon: Enjoy lunch at a traditional restaurant\n"
            itinerary_text += f"- Afternoon: Explore the area\n"
            itinerary_text += f"- Evening: Dinner and cultural experience\n\n"
        
        if interests:
            itinerary_text += f"Special recommendations based on your interests:\n"
            for interest in interests:
                itinerary_text += f"- {interest.capitalize()} activities: Sample activity based on {interest}\n"
        
        return itinerary_text