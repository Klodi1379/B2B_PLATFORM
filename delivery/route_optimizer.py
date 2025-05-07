"""
Route optimization module for delivery planning.
Supports multiple route optimization services:
- GraphHopper
- OpenRouteService
"""

import requests
import json
import logging
from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

class RouteOptimizer:
    """Base class for route optimization services"""

    def optimize_route(self, start_point, stops, return_to_start=True):
        """
        Optimize a route with multiple stops

        Args:
            start_point: Dict with lat and lng of starting point
            stops: List of dicts with stop information (id, lat, lng)
            return_to_start: Whether to return to the starting point

        Returns:
            Dict with optimized route information
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_distance_matrix(self, points):
        """
        Get a distance matrix between all points

        Args:
            points: List of dicts with lat and lng

        Returns:
            Matrix of distances between points
        """
        raise NotImplementedError("Subclasses must implement this method")


class GraphHopperOptimizer(RouteOptimizer):
    """GraphHopper implementation of route optimization"""

    def __init__(self):
        self.api_key = getattr(settings, 'GRAPHHOPPER_API_KEY', '')
        self.base_url = "https://graphhopper.com/api/1"

    def optimize_route(self, start_point, stops, return_to_start=True):
        """Optimize route using GraphHopper Vehicle Routing API"""

        if not stops:
            return {
                'route': [],
                'total_distance': 0,
                'total_time': 0,
            }

        try:
            # For simple cases (few stops), we can use the Directions API instead of VRP
            if len(stops) <= 10:
                return self._optimize_with_directions(start_point, stops, return_to_start)

            # For more complex cases, use the VRP API
            # Prepare the request payload
            vehicles = [{
                "vehicle_id": "delivery_vehicle",
                "start_address": {
                    "location_id": "depot",
                    "lat": float(start_point['lat']),
                    "lon": float(start_point['lng'])
                }
            }]

            if return_to_start:
                vehicles[0]["end_address"] = vehicles[0]["start_address"]

            # Prepare services (stops)
            services = []
            for i, stop in enumerate(stops):
                services.append({
                    "id": f"stop_{stop['id']}",
                    "name": f"Stop {i+1}",
                    "address": {
                        "location_id": f"stop_{stop['id']}",
                        "lat": float(stop['lat']),
                        "lon": float(stop['lng'])
                    }
                })

            # Build the full request
            payload = {
                "vehicles": vehicles,
                "services": services,
                "objectives": ["transport_time"]
            }

            # Make the API request
            url = f"{self.base_url}/vrp?key={self.api_key}"
            response = requests.post(url, json=payload)

            if response.status_code != 200:
                logger.error(f"GraphHopper API error: {response.text}")
                # Fall back to directions API
                return self._optimize_with_directions(start_point, stops, return_to_start)

            # Process the response
            result = response.json()

            # Extract the optimized route
            route = []
            if 'solution' in result and 'routes' in result['solution']:
                for activity in result['solution']['routes'][0]['activities']:
                    if activity['type'] == 'service':
                        stop_id = int(activity['id'].replace('stop_', ''))
                        route.append({
                            'stop_id': stop_id,
                            'arrival_time': activity.get('arrival_time', 0),
                            'distance': activity.get('distance', 0)
                        })

            return {
                'route': route,
                'total_distance': result['solution']['routes'][0]['distance'] / 1000,  # Convert to km
                'total_time': result['solution']['routes'][0]['transport_time'] / 60,  # Convert to minutes
            }

        except Exception as e:
            logger.exception(f"Error in GraphHopper optimization: {str(e)}")
            # Fall back to a simple nearest neighbor algorithm
            return self._optimize_with_nearest_neighbor(start_point, stops, return_to_start)

    def _optimize_with_directions(self, start_point, stops, return_to_start=True):
        """Use GraphHopper Directions API for route optimization"""
        try:
            # Prepare points
            points = [f"{start_point['lat']},{start_point['lng']}"]
            for stop in stops:
                points.append(f"{stop['lat']},{stop['lng']}")

            if return_to_start:
                points.append(points[0])  # Add start point as end point

            # Build the request URL
            url = f"{self.base_url}/route?key={self.api_key}&profile=car&points_encoded=false"
            for point in points:
                url += f"&point={point}"

            # Add optimization parameter
            url += "&algorithm=alternative_route&ch.disable=true"

            # Make the API request
            response = requests.get(url)

            if response.status_code != 200:
                logger.error(f"GraphHopper Directions API error: {response.text}")
                # Fall back to nearest neighbor
                return self._optimize_with_nearest_neighbor(start_point, stops, return_to_start)

            # Process the response
            result = response.json()

            # Extract the optimized route
            route = []
            for i, stop in enumerate(stops):
                route.append({
                    'stop_id': stop['id'],
                    'position': i + 1
                })

            # Get total distance and time
            path = result['paths'][0]
            total_distance = path['distance'] / 1000  # Convert to km
            total_time = path['time'] / (1000 * 60)  # Convert to minutes

            return {
                'route': route,
                'total_distance': total_distance,
                'total_time': total_time,
            }

        except Exception as e:
            logger.exception(f"Error in GraphHopper directions: {str(e)}")
            # Fall back to a simple nearest neighbor algorithm
            return self._optimize_with_nearest_neighbor(start_point, stops, return_to_start)

    def _optimize_with_nearest_neighbor(self, start_point, stops, return_to_start=True):
        """Simple nearest neighbor algorithm for route optimization"""
        try:
            # Get distance matrix
            all_points = [start_point] + [{'lat': stop['lat'], 'lng': stop['lng']} for stop in stops]
            matrix = self.get_distance_matrix(all_points)

            # Implement a simple nearest neighbor algorithm
            current_point = 0  # Start at the depot
            unvisited = list(range(1, len(all_points)))  # Skip the depot
            route_order = []
            total_distance = 0
            total_time = 0

            while unvisited:
                # Find the nearest unvisited point
                nearest = min(unvisited, key=lambda i: matrix['distances'][current_point][i])
                route_order.append(nearest)
                total_distance += matrix['distances'][current_point][nearest]
                total_time += matrix['times'][current_point][nearest]
                current_point = nearest
                unvisited.remove(nearest)

            # Return to start if needed
            if return_to_start:
                total_distance += matrix['distances'][current_point][0]
                total_time += matrix['times'][current_point][0]

            # Map the route order back to stop IDs
            route = []
            for i, point_idx in enumerate(route_order):
                stop_id = stops[point_idx - 1]['id']  # -1 because we added the depot at the beginning
                route.append({
                    'stop_id': stop_id,
                    'position': i + 1
                })

            return {
                'route': route,
                'total_distance': total_distance / 1000,  # Convert to km
                'total_time': total_time / 60,  # Convert to minutes
            }

        except Exception as e:
            logger.exception(f"Error in nearest neighbor optimization: {str(e)}")
            # Just return the stops in their original order as a last resort
            route = []
            for i, stop in enumerate(stops):
                route.append({
                    'stop_id': stop['id'],
                    'position': i + 1
                })

            return {
                'route': route,
                'total_distance': 0,
                'total_time': 0,
            }

    def get_distance_matrix(self, points):
        """Get distance matrix using GraphHopper Matrix API"""

        try:
            # Prepare points
            points_str = []
            for point in points:
                points_str.append(f"{point['lat']},{point['lng']}")

            # Make the API request
            url = f"{self.base_url}/matrix?key={self.api_key}&type=json&vehicle=car"
            payload = {
                "points": points_str,
                "out_arrays": ["distances", "times"]
            }

            response = requests.post(url, json=payload)

            if response.status_code != 200:
                logger.error(f"GraphHopper Matrix API error: {response.text}")
                # Return a simple Euclidean distance matrix as fallback
                return self._get_euclidean_matrix(points)

            result = response.json()

            return {
                'distances': result['distances'],  # Matrix of distances in meters
                'times': result['times']  # Matrix of times in seconds
            }

        except Exception as e:
            logger.exception(f"Error in GraphHopper matrix: {str(e)}")
            # Return a simple Euclidean distance matrix as fallback
            return self._get_euclidean_matrix(points)

    def _get_euclidean_matrix(self, points):
        """Calculate a simple Euclidean distance matrix"""
        import math

        n = len(points)
        distances = [[0 for _ in range(n)] for _ in range(n)]
        times = [[0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    # Calculate Euclidean distance
                    dx = 111.32 * (float(points[i]['lng']) - float(points[j]['lng'])) * math.cos(math.radians((float(points[i]['lat']) + float(points[j]['lat'])) / 2))
                    dy = 110.57 * (float(points[i]['lat']) - float(points[j]['lat']))
                    distance = math.sqrt(dx*dx + dy*dy) * 1000  # Convert to meters

                    # Estimate time (assuming 50 km/h average speed)
                    time = (distance / 1000) / 50 * 3600  # Convert to seconds

                    distances[i][j] = distance
                    times[i][j] = time

        return {
            'distances': distances,
            'times': times
        }


class OpenRouteServiceOptimizer(RouteOptimizer):
    """OpenRouteService implementation of route optimization"""

    def __init__(self):
        self.api_key = getattr(settings, 'OPENROUTE_API_KEY', '')
        self.base_url = "https://api.openrouteservice.org"

    def optimize_route(self, start_point, stops, return_to_start=True):
        """
        Optimize route using OpenRouteService Optimization API
        Note: ORS doesn't have a direct VRP solver, so we'll use the directions API
        with the optimize_waypoints parameter
        """
        if not stops:
            return {
                'route': [],
                'total_distance': 0,
                'total_time': 0,
            }

        try:
            # Prepare coordinates (ORS uses [lng, lat] format)
            coordinates = [[float(start_point['lng']), float(start_point['lat'])]]

            for stop in stops:
                coordinates.append([float(stop['lng']), float(stop['lat'])])

            if return_to_start:
                coordinates.append(coordinates[0])  # Add start point as end point

            # Make the API request
            url = f"{self.base_url}/v2/directions/driving-car"
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                "coordinates": coordinates,
                "optimize_waypoints": True,
                "instructions": False,
                "preference": "fastest"
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"OpenRouteService API error: {response.text}")
                # Fall back to nearest neighbor
                return self._optimize_with_nearest_neighbor(start_point, stops, return_to_start)

            result = response.json()

            # Get the optimized waypoint order
            waypoint_order = result.get('metadata', {}).get('query', {}).get('waypoints', [])

            # If we got a valid waypoint order, use it
            if waypoint_order and len(waypoint_order) >= len(stops):
                # The waypoint order includes the start and end points, so we need to adjust
                # Extract just the stops (exclude start and end points if returning to start)
                if return_to_start:
                    # Remove first and last points (start and end)
                    stop_indices = waypoint_order[1:-1]
                else:
                    # Remove just the first point (start)
                    stop_indices = waypoint_order[1:]

                # Map the indices to stop IDs
                route = []
                for i, idx in enumerate(stop_indices):
                    # Adjust index (subtract 1 because idx 0 is the start point)
                    adjusted_idx = idx - 1
                    if 0 <= adjusted_idx < len(stops):
                        route.append({
                            'stop_id': stops[adjusted_idx]['id'],
                            'position': i + 1
                        })
            else:
                # If we didn't get a valid waypoint order, just use the original order
                route = []
                for i, stop in enumerate(stops):
                    route.append({
                        'stop_id': stop['id'],
                        'position': i + 1
                    })

            # Get total distance and time
            summary = result['routes'][0]['summary']
            total_distance = summary['distance'] / 1000  # Convert to km
            total_time = summary['duration'] / 60  # Convert to minutes

            return {
                'route': route,
                'total_distance': total_distance,
                'total_time': total_time,
            }

        except Exception as e:
            logger.exception(f"Error in OpenRouteService optimization: {str(e)}")
            # Fall back to a simple nearest neighbor algorithm
            return self._optimize_with_nearest_neighbor(start_point, stops, return_to_start)

    def _optimize_with_nearest_neighbor(self, start_point, stops, return_to_start=True):
        """Simple nearest neighbor algorithm for route optimization"""
        try:
            # Get distance matrix
            all_points = [start_point] + [{'lat': stop['lat'], 'lng': stop['lng']} for stop in stops]
            matrix = self.get_distance_matrix(all_points)

            # Implement a simple nearest neighbor algorithm
            current_point = 0  # Start at the depot
            unvisited = list(range(1, len(all_points)))  # Skip the depot
            route_order = []
            total_distance = 0
            total_time = 0

            while unvisited:
                # Find the nearest unvisited point
                nearest = min(unvisited, key=lambda i: matrix['distances'][current_point][i])
                route_order.append(nearest)
                total_distance += matrix['distances'][current_point][nearest]
                total_time += matrix['times'][current_point][nearest]
                current_point = nearest
                unvisited.remove(nearest)

            # Return to start if needed
            if return_to_start:
                total_distance += matrix['distances'][current_point][0]
                total_time += matrix['times'][current_point][0]

            # Map the route order back to stop IDs
            route = []
            for i, point_idx in enumerate(route_order):
                stop_id = stops[point_idx - 1]['id']  # -1 because we added the depot at the beginning
                route.append({
                    'stop_id': stop_id,
                    'position': i + 1
                })

            return {
                'route': route,
                'total_distance': total_distance / 1000,  # Convert to km
                'total_time': total_time / 60,  # Convert to minutes
            }

        except Exception as e:
            logger.exception(f"Error in nearest neighbor optimization: {str(e)}")
            # Just return the stops in their original order as a last resort
            route = []
            for i, stop in enumerate(stops):
                route.append({
                    'stop_id': stop['id'],
                    'position': i + 1
                })

            return {
                'route': route,
                'total_distance': 0,
                'total_time': 0,
            }

    def get_distance_matrix(self, points):
        """Get distance matrix using OpenRouteService Matrix API"""

        try:
            # Prepare coordinates (ORS uses [lng, lat] format)
            coordinates = [[float(point['lng']), float(point['lat'])] for point in points]

            # Make the API request
            url = f"{self.base_url}/v2/matrix/driving-car"
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                "locations": coordinates,
                "metrics": ["distance", "duration"],
                "units": "m"
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"OpenRouteService Matrix API error: {response.text}")
                # Return a simple Euclidean distance matrix as fallback
                return self._get_euclidean_matrix(points)

            result = response.json()

            return {
                'distances': result['distances'],  # Matrix of distances in meters
                'times': result['durations']  # Matrix of times in seconds
            }

        except Exception as e:
            logger.exception(f"Error in OpenRouteService matrix: {str(e)}")
            # Return a simple Euclidean distance matrix as fallback
            return self._get_euclidean_matrix(points)

    def _get_euclidean_matrix(self, points):
        """Calculate a simple Euclidean distance matrix"""
        import math

        n = len(points)
        distances = [[0 for _ in range(n)] for _ in range(n)]
        times = [[0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    # Calculate Euclidean distance
                    dx = 111.32 * (float(points[i]['lng']) - float(points[j]['lng'])) * math.cos(math.radians((float(points[i]['lat']) + float(points[j]['lat'])) / 2))
                    dy = 110.57 * (float(points[i]['lat']) - float(points[j]['lat']))
                    distance = math.sqrt(dx*dx + dy*dy) * 1000  # Convert to meters

                    # Estimate time (assuming 50 km/h average speed)
                    time = (distance / 1000) / 50 * 3600  # Convert to seconds

                    distances[i][j] = distance
                    times[i][j] = time

        return {
            'distances': distances,
            'times': times
        }


def get_optimizer():
    """Factory function to get the configured optimizer"""
    optimizer_type = getattr(settings, 'ROUTE_OPTIMIZER', 'graphhopper')

    if optimizer_type.lower() == 'openrouteservice':
        return OpenRouteServiceOptimizer()
    else:
        return GraphHopperOptimizer()
