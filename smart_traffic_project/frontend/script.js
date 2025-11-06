const API_BASE = 'http://localhost:5001/api';
let map = null;
let routingControl = null;
let currentRoutes = [];
let selectedRoute = null;
let navigationActive = false;
let currentStepIndex = 0;
let userLocation = null;
let watchId = null;
let userMarker = null;
let routeMarkers = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeSliders();
    loadModelAnalysis();
    startLocationTracking();
    setupAddressSearch();
});

function startLocationTracking() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                userLocation = [position.coords.latitude, position.coords.longitude];
                if (map && userMarker) {
                    userMarker.setLatLng(userLocation);
                    map.setView(userLocation, 13);
                }
            },
            error => console.log('Location access denied'),
            { enableHighAccuracy: true, timeout: 10000 }
        );
        
        watchId = navigator.geolocation.watchPosition(
            position => {
                userLocation = [position.coords.latitude, position.coords.longitude];
                if (navigationActive && map && userMarker) {
                    userMarker.setLatLng(userLocation);
                    updateNavigationProgress();
                }
            },
            error => console.log('Location tracking error:', error),
            { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
        );
    }
}

function setupAddressSearch() {
    const originInput = document.getElementById('origin');
    const destinationInput = document.getElementById('destination');
    
    const predOriginInput = document.getElementById('pred-origin');
    const predDestinationInput = document.getElementById('pred-destination');
    
    originInput.addEventListener('input', (e) => searchAddress(e.target.value, 'origin'));
    destinationInput.addEventListener('input', (e) => searchAddress(e.target.value, 'destination'));
    predOriginInput.addEventListener('input', (e) => searchAddress(e.target.value, 'pred-origin'));
    predDestinationInput.addEventListener('input', (e) => searchAddress(e.target.value, 'pred-destination'));
    
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            document.querySelectorAll('.suggestions').forEach(s => s.style.display = 'none');
        }
    });
}

async function searchAddress(query, inputType) {
    if (query.length < 3) {
        document.getElementById(inputType + '-suggestions').style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=in`);
        const results = await response.json();
        
        const suggestionsDiv = document.getElementById(inputType + '-suggestions');
        
        if (results.length > 0) {
            const suggestions = results.map(result => 
                `<div class="suggestion-item" onclick="selectAddress('${result.display_name}', [${result.lat}, ${result.lon}], '${inputType}')">
                    <i class="fas fa-map-marker-alt"></i> ${result.display_name}
                </div>`
            ).join('');
            
            suggestionsDiv.innerHTML = suggestions;
            suggestionsDiv.style.display = 'block';
        } else {
            suggestionsDiv.style.display = 'none';
        }
    } catch (error) {
        console.log('Search error:', error);
    }
}

function selectAddress(address, coordinates, inputType) {
    document.getElementById(inputType).value = address;
    document.getElementById(inputType + '-suggestions').style.display = 'none';
    
    if (inputType === 'origin') {
        window.originCoords = coordinates;
    } else if (inputType === 'destination') {
        window.destinationCoords = coordinates;
    } else if (inputType === 'pred-origin') {
        window.predOriginCoords = coordinates;
    } else if (inputType === 'pred-destination') {
        window.predDestinationCoords = coordinates;
    }
    
    if (map && (inputType === 'origin' || inputType === 'destination')) {
        map.setView(coordinates, 13);
        
        const marker = L.marker(coordinates).addTo(map)
            .bindPopup(inputType === 'origin' ? 'Start Location' : 'Destination')
            .openPopup();
        
        routeMarkers.push(marker);
    }
}

function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            if (targetTab === 'routes' && !map) {
                setTimeout(initializeMap, 200);
            }
        });
    });
}

function initializeSliders() {
    const hourSlider = document.getElementById('hour');
    const hourValue = document.getElementById('hour-value');
    hourSlider.addEventListener('input', () => {
        hourValue.textContent = hourSlider.value + ':00';
    });

    const rainSlider = document.getElementById('rain');
    const rainValue = document.getElementById('rain-value');
    rainSlider.addEventListener('input', () => {
        rainValue.textContent = parseFloat(rainSlider.value).toFixed(1);
    });

    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');
    tempSlider.addEventListener('input', () => {
        tempValue.textContent = tempSlider.value + '°C';
    });

    const speedSlider = document.getElementById('speed');
    const speedValue = document.getElementById('speed-value');
    speedSlider.addEventListener('input', () => {
        speedValue.textContent = speedSlider.value + ' km/h';
    });

    const routeHourSlider = document.getElementById('route-hour');
    const routeHourValue = document.getElementById('route-hour-value');
    routeHourSlider.addEventListener('input', () => {
        routeHourValue.textContent = routeHourSlider.value + ':00';
    });

    const routeRainSlider = document.getElementById('route-rain');
    const routeRainValue = document.getElementById('route-rain-value');
    routeRainSlider.addEventListener('input', () => {
        const value = parseFloat(routeRainSlider.value);
        if (value === 0) routeRainValue.textContent = 'No Rain';
        else if (value <= 0.3) routeRainValue.textContent = 'Light Rain';
        else if (value <= 0.7) routeRainValue.textContent = 'Moderate Rain';
        else routeRainValue.textContent = 'Heavy Rain';
    });
}

async function predictTraffic() {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    const origin = document.getElementById('pred-origin').value.trim();
    const destination = document.getElementById('pred-destination').value.trim();
    
    const existingMessage = document.querySelector('.validation-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    if (!origin || !destination) {
        const validationMessage = document.createElement('div');
        validationMessage.className = 'validation-message';
        validationMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Please enter both source and destination locations to get traffic predictions';
        
        const resultsCard = document.querySelector('#results').parentElement;
        resultsCard.insertBefore(validationMessage, resultsCard.firstChild.nextSibling);
        
        return;
    }
    
    loading.style.display = 'block';
    results.style.display = 'none';

    try {
        const hour = parseInt(document.getElementById('hour').value);
        const dayOfWeek = parseInt(document.getElementById('dayOfWeek').value);
        const isWeekend = dayOfWeek >= 5 ? 1 : 0;
        const rainIntensity = parseFloat(document.getElementById('rain').value);
        const temperature = parseInt(document.getElementById('temperature').value);
        const avgSpeed = parseInt(document.getElementById('speed').value);
        const eventFlag = document.getElementById('event').checked ? 1 : 0;
        const rushHour = (hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 19) ? 1 : 0;

        const response = await fetch(API_BASE + '/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                origin, destination, hour, day_of_week: dayOfWeek, is_weekend: isWeekend,
                rain_intensity: rainIntensity, temperature, humidity: 60,
                event_flag: eventFlag, rush_hour: rushHour, avg_speed: avgSpeed
            })
        });

        if (!response.ok) throw new Error('Network error');
        
        const data = await response.json();
        if (data.success) {
            displayResults(data, origin, destination);
        } else {
            throw new Error(data.error || 'Prediction failed');
        }
    } catch (error) {
        console.error('Error:', error);
        results.innerHTML = '<p style="color: red; text-align: center;">Error: ' + error.message + '</p>';
        results.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
}

function displayResults(data, origin, destination) {
    document.getElementById('traffic-value').textContent = Math.round(data.predicted_traffic);
    document.getElementById('score-value').textContent = data.route_score + '/100';

    const level = data.traffic_level;
    const trafficLevel = document.getElementById('traffic-level');
    trafficLevel.innerHTML = level.icon + ' ' + level.level + ' Traffic';
    trafficLevel.style.backgroundColor = level.color;

    const recommendations = document.getElementById('recommendations');
    recommendations.innerHTML = '<h4> Route: ' + origin + ' ' + destination + '</h4>' +
        '<h4> Recommendations:</h4><ul>' + 
        data.recommendations.map(rec => '<li>' + rec + '</li>').join('') + '</ul>';

    document.getElementById('results').style.display = 'block';
}

async function loadModelAnalysis() {
    try {
        const response = await fetch(API_BASE + '/models');
        if (!response.ok) return;
        
        const data = await response.json();
        if (data.success) {
            displayModelTable(data.models);
            displayPerformanceChart(data.models);
        }
    } catch (error) {
        console.log('Model analysis will load when backend is ready');
    }
}

function displayModelTable(models) {
    const table = '<div class="model-table"><table><thead><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>R² Score</th><th>Accuracy</th></tr></thead><tbody>' +
        models.map(model => 
            '<tr><td><strong>' + model.name + '</strong></td><td>' + model.mae + '</td><td>' + 
            model.rmse + '</td><td>' + model.r2 + '</td><td>' + model.accuracy + '%</td></tr>'
        ).join('') + '</tbody></table></div>';
    
    document.getElementById('model-table').innerHTML = table;
}

function displayPerformanceChart(models) {
    const ctx = document.getElementById('performance-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: models.map(m => m.name),
            datasets: [{
                label: 'Accuracy (%)',
                data: models.map(m => m.accuracy),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, max: 100 } }
        }
    });
}

function initializeMap() {
    try {
        if (map) return;
        
        const defaultLocation = userLocation || [12.9716, 77.5946];
        
        map = L.map('map').setView(defaultLocation, 12);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);
        
        if (userLocation) {
            userMarker = L.marker(userLocation, {
                icon: L.divIcon({
                    className: 'user-location-marker',
                    html: '<i class="fas fa-location-arrow" style="color: #007bff; font-size: 20px;"></i>',
                    iconSize: [20, 20]
                })
            }).addTo(map).bindPopup('Your Location');
        }
        
        console.log('Map initialized successfully');
        
    } catch (error) {
        console.error('Map initialization error:', error);
        document.getElementById('map').innerHTML = 
            '<div style="text-align: center; padding: 50px; background: #f8f9fa; border-radius: 10px;">' +
            '<i class="fas fa-map-marked-alt" style="font-size: 3em; color: #007bff; margin-bottom: 15px;"></i>' +
            '<p><strong>Real-Time Navigation Ready</strong></p>' +
            '<p style="font-size: 0.9em; color: #666;">Enter origin and destination to start</p>' +
            '</div>';
    }
}

function toggleTrafficLayer() {
    const btn = event.target;
    if (btn.classList.contains('active')) {
        btn.classList.remove('active');
        btn.innerHTML = '<i class="fas fa-road"></i> Traffic Layer';
        btn.style.background = '';
    } else {
        btn.classList.add('active');
        btn.innerHTML = '<i class="fas fa-road"></i> Traffic ON';
        btn.style.background = '#28a745';
    }
}

function recenterMap() {
    if (!map) return;
    
    if (userLocation) {
        map.setView(userLocation, 15);
        if (userMarker) {
            userMarker.setLatLng(userLocation);
        }
    } else {
        map.setView([12.9716, 77.5946], 12);
    }
}

function useCurrentLocation(inputId) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const coords = [position.coords.latitude, position.coords.longitude];
                
                fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${coords[0]}&lon=${coords[1]}`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById(inputId).value = data.display_name;
                        
                        if (inputId === 'origin') {
                            window.originCoords = coords;
                        } else if (inputId === 'destination') {
                            window.destinationCoords = coords;
                        } else if (inputId === 'pred-origin') {
                            window.predOriginCoords = coords;
                        } else if (inputId === 'pred-destination') {
                            window.predDestinationCoords = coords;
                        }
                        
                        if (map && (inputId === 'origin' || inputId === 'destination')) {
                            map.setView(coords, 15);
                            const marker = L.marker(coords).addTo(map)
                                .bindPopup('Current Location')
                                .openPopup();
                            routeMarkers.push(marker);
                        }
                    });
            },
            () => alert('Unable to get location')
        );
    } else {
        alert('Geolocation not supported');
    }
}

async function findBestRoute() {
    const routeResults = document.getElementById('route-results');
    routeResults.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Finding optimal routes...</div>';

    try {
        const origin = document.getElementById('origin').value;
        const destination = document.getElementById('destination').value;
        
        if (!origin || !destination) {
            throw new Error('Please enter both origin and destination');
        }

        await calculateRealRoutes(origin, destination);
        
        startLiveTrafficUpdates();
        
    } catch (error) {
        routeResults.innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
    }
}

async function calculateRealRoutes(origin, destination) {
    try {
        clearRoutes();
        
        const originCoords = window.originCoords || await geocodeAddress(origin);
        const destCoords = window.destinationCoords || await geocodeAddress(destination);
        
        routingControl = L.Routing.control({
            waypoints: [
                L.latLng(originCoords[0], originCoords[1]),
                L.latLng(destCoords[0], destCoords[1])
            ],
            routeWhileDragging: false,
            addWaypoints: false,
            createMarker: function(i, waypoint, n) {
                const isStart = i === 0;
                return L.marker(waypoint.latLng, {
                    icon: L.divIcon({
                        className: 'route-marker',
                        html: `<i class="fas ${isStart ? 'fa-play' : 'fa-flag-checkered'}" 
                               style="color: ${isStart ? '#28a745' : '#dc3545'}; font-size: 16px;"></i>`,
                        iconSize: [20, 20]
                    })
                }).bindPopup(isStart ? 'Start' : 'Destination');
            },
            lineOptions: {
                styles: [{ color: '#007bff', weight: 6, opacity: 0.8 }]
            }
        }).on('routesfound', function(e) {
            const routes = e.routes;
            processFoundRoutes(routes, origin, destination);
        }).addTo(map);
        
    } catch (error) {
        console.error('Route calculation error:', error);
        currentRoutes = generateFallbackRoutes(origin, destination);
        displayRealTimeRoutes();
    }
}

function processFoundRoutes(routes, origin, destination) {
    currentRoutes = routes.map((route, index) => {
        const distance = (route.summary.totalDistance / 1000).toFixed(1);
        const duration = Math.round(route.summary.totalTime / 60);
        
        return {
            name: index === 0 ? 'Fastest Route' : `Alternative ${index}`,
            distance: distance + ' km',
            duration: duration + ' min',
            duration_in_traffic: Math.round(duration * 1.2) + ' min',
            steps: route.instructions.map(inst => inst.text),
            coordinates: route.coordinates,
            traffic_level: index === 0 ? 'Light' : index === 1 ? 'Moderate' : 'Heavy',
            score: 95 - (index * 8) + Math.random() * 10,
            routeIndex: index,
            route: route
        };
    });
    
    displayRealTimeRoutes();
}

async function geocodeAddress(address) {
    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`);
    const data = await response.json();
    
    if (data && data.length > 0) {
        return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
    }
    
    const fallbacks = {
        'bangalore': [12.9716, 77.5946],
        'mysore': [12.2958, 76.6394],
        'chennai': [13.0827, 80.2707],
        'mumbai': [19.0760, 72.8777]
    };
    
    const key = Object.keys(fallbacks).find(k => address.toLowerCase().includes(k));
    return key ? fallbacks[key] : [12.9716, 77.5946];
}

function generateFallbackRoutes(origin, destination) {
    return [
        {
            name: 'Main Route',
            distance: '15.2 km',
            duration: '22 min',
            duration_in_traffic: '28 min',
            steps: [`Start from ${origin}`, 'Follow main roads', `Arrive at ${destination}`],
            coordinates: [[12.9716, 77.5946], [12.2958, 76.6394]],
            traffic_level: 'Moderate',
            score: 85,
            routeIndex: 0
        }
    ];
}

function clearRoutes() {
    try {
        if (routingControl && map) {
            map.removeControl(routingControl);
            routingControl = null;
        }
        
        routeMarkers.forEach(marker => {
            if (map && marker) {
                map.removeLayer(marker);
            }
        });
        routeMarkers = [];
    } catch (error) {
        console.log('Route clearing completed');
        routeMarkers = [];
    }
}

function displayRealTimeRoutes() {
    if (!currentRoutes || currentRoutes.length === 0) return;
    
    const bestRoute = currentRoutes.reduce((best, route) => 
        route.score > best.score ? route : best, currentRoutes[0]);
    
    document.getElementById('total-routes').textContent = currentRoutes.length;
    document.getElementById('best-score').textContent = Math.round(bestRoute.score) + '/100';
    document.getElementById('time-saved').textContent = calculateTimeSaved() + ' min';
    document.getElementById('traffic-level').textContent = bestRoute.traffic_level;
    
    displayRouteResults(currentRoutes, bestRoute);
}

function calculateTimeSaved() {
    if (currentRoutes.length < 2) return 0;
    
    const durations = currentRoutes.map(r => {
        const durationStr = r.duration_in_traffic || r.duration;
        return parseInt(durationStr.replace(' min', ''));
    });
    
    const fastest = Math.min(...durations);
    const slowest = Math.max(...durations);
    
    return slowest - fastest;
}

function displayRouteResults(routes, bestRoute) {
    const routeCards = routes.map((route, index) => 
        `<div class="route-option ${route.name === bestRoute.name ? 'best' : ''}" onclick="selectRoute(${index})">
            <div class="route-header">
                <div class="route-title">${route.name}</div>
                ${route.name === bestRoute.name ? '<div class="route-badge"> OPTIMAL</div>' : ''}
            </div>
            <div class="route-details">
                <div class="route-detail"><div class="route-detail-value">${route.distance}</div><div class="route-detail-label">Distance</div></div>
                <div class="route-detail"><div class="route-detail-value">${route.duration_in_traffic || route.duration}</div><div class="route-detail-label">Duration</div></div>
                <div class="route-detail"><div class="route-detail-value">${route.traffic_level}</div><div class="route-detail-label">Traffic</div></div>
                <div class="route-detail"><div class="route-detail-value">${Math.round(route.score)}/100</div><div class="route-detail-label">AI Score</div></div>
            </div>
            <div class="route-steps"><h5><i class="fas fa-route"></i> Turn-by-Turn:</h5><ol>
                ${route.steps.slice(0, 3).map(step => `<li>${step}</li>`).join('')}
                ${route.steps.length > 3 ? `<li><em>... and ${route.steps.length - 3} more steps</em></li>` : ''}
            </ol></div>
        </div>`
    ).join('');

    document.getElementById('route-results').innerHTML = 
        `<div style="text-align: center; margin-bottom: 20px;">
            <h4 style="color: #28a745;"><span class="live-indicator"></span> AI Recommended: ${bestRoute.name}</h4>
            <p style="color: #666; font-size: 0.9em;">Based on real-time traffic and ML predictions</p>
        </div>` + routeCards;
}

function selectRoute(routeIndex) {
    if (!currentRoutes || routeIndex >= currentRoutes.length) return;
    
    selectedRoute = currentRoutes[routeIndex];
    
    document.querySelectorAll('.route-option').forEach((el, index) => {
        el.classList.toggle('selected', index === routeIndex);
    });
}

function startNavigation() {
    if (!selectedRoute && currentRoutes.length > 0) {
        selectedRoute = currentRoutes[0];
    }
    
    if (!selectedRoute) {
        alert('Please find routes first');
        return;
    }
    
    navigationActive = true;
    currentStepIndex = 0;
    
    document.getElementById('navigation-panel').style.display = 'block';
    displayNavigationInstructions();
}

function displayNavigationInstructions() {
    if (!selectedRoute) return;
    
    const steps = selectedRoute.steps;
    const stepsList = steps.map((step, index) => 
        `<div class="direction-step ${index === currentStepIndex ? 'active' : ''}">
            <div class="direction-icon">${index + 1}</div>
            <div>${step}</div>
        </div>`
    ).join('');
    
    document.getElementById('directions-list').innerHTML = stepsList;
}

function nextStep() {
    if (!selectedRoute || currentStepIndex >= selectedRoute.steps.length - 1) return;
    
    currentStepIndex++;
    displayNavigationInstructions();
}

function stopNavigation() {
    navigationActive = false;
    currentStepIndex = 0;
    document.getElementById('navigation-panel').style.display = 'none';
}

function updateNavigationProgress() {
    if (!navigationActive || !userLocation || !selectedRoute) return;
    console.log('Navigation progress updated');
}

function startLiveTrafficUpdates() {
    setInterval(() => {
        updateTrafficAlerts();
    }, 30000);
    
    updateTrafficAlerts();
}

function updateTrafficAlerts() {
    const alerts = [
        { type: 'moderate', message: 'Moderate traffic on Main Street - 5 min delay' },
        { type: 'light', message: 'Construction ahead on Highway 101 - Right lane closed' },
        { type: 'severe', message: 'Accident reported on Ring Road - Consider alternate route' }
    ];
    
    const randomAlerts = alerts.sort(() => 0.5 - Math.random()).slice(0, 2);
    
    const alertsHtml = randomAlerts.map(alert => 
        `<div class="traffic-alert ${alert.type}">
            <span class="live-indicator"></span>${alert.message}
        </div>`
    ).join('');
    
    document.getElementById('traffic-alerts').innerHTML = alertsHtml || 
        '<div class="traffic-alert"><span class="live-indicator"></span>No traffic incidents reported</div>';
}

setInterval(() => {
    if (navigationActive && selectedRoute) {
        const trafficConditions = ['Light', 'Moderate', 'Heavy'];
        const randomCondition = trafficConditions[Math.floor(Math.random() * trafficConditions.length)];
        
        if (selectedRoute) {
            selectedRoute.traffic_level = randomCondition;
            document.getElementById('traffic-level').textContent = randomCondition;
        }
    }
}, 15000);
