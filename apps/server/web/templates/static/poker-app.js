let config = {
    backend_capture_interval: 3,  // Updated to match client default
    show_table_cards: true,
    show_positions: true,
    show_moves: true,
    show_solver_link: true
};

// Simple dynamic table management
let previousDetections = [];

function copyToClipboard(text) {
    // Remove any whitespace so copied hand is contiguous (e.g. "ackd7s2h")
    const normalized = text ? text.replace(/\s+/g, '') : '';

    navigator.clipboard.writeText(normalized).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy!');
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

function showUpdateIndicator() {
    const indicator = document.getElementById('updateIndicator');
    indicator.classList.add('show');
    setTimeout(() => {
        indicator.classList.remove('show');
    }, 1000);
}

function updateConnectionStatus(status, message) {
    const statusEl = document.getElementById('connectionStatus');
    statusEl.className = `connection-status ${status}`;
    statusEl.textContent = message;
}

function getSuitColor(card) {
    const suit = card.slice(-1);
    if (suit === '♥') return 'red';
    if (suit === '♦') return 'blue';
    if (suit === '♣') return 'green';
    return 'black';
}

function detectChanges(newDetections) {
    const newStr = JSON.stringify(newDetections);
    const prevStr = JSON.stringify(previousDetections);
    return newStr !== prevStr;
}

function createPlayerCardsSection(detection, isUpdate) {
    const cardsClass = isUpdate ? 'cards-block new-cards' : 'cards-block';

    if (detection.player_cards && detection.player_cards.length > 0) {
        const cardsHtml = detection.player_cards.map(card =>
            `<div class="card ${getSuitColor(card.display)}">${card.display}</div>`
        ).join('');

        return `<div class="${cardsClass}" onclick="copyToClipboard('${detection.player_cards_string}')">${cardsHtml}</div>`;
    }

    return '<div class="no-cards">No cards detected</div>';
}

function createTableCardsSection(detection, isUpdate) {
    if (!config.show_table_cards) {
        return '';
    }

    const cardsClass = isUpdate ? 'cards-block new-cards' : 'cards-block';
    const streetClass = detection.street && detection.street.startsWith('ERROR') ? 'street-indicator error' : 'street-indicator';
    const streetDisplay = detection.street ? `<span class="${streetClass}">${detection.street}</span>` : '';

    let cardsHtml = '';
    if (detection.table_cards && detection.table_cards.length > 0) {
        const cards = detection.table_cards.map(card =>
            `<div class="card ${getSuitColor(card.display)}">${card.display}</div>`
        ).join('');
        cardsHtml = `<div class="${cardsClass}" onclick="copyToClipboard('${detection.table_cards_string}')">${cards}</div>`;
    } else {
        cardsHtml = '<div class="no-cards">No cards detected</div>';
    }

    return `
        <div class="table-cards-column">
            <div class="cards-label">Table Cards: ${streetDisplay}</div>
            <div class="cards-container">${cardsHtml}</div>
        </div>
    `;
}

function createPositionsSection(detection, isUpdate) {
    if (!config.show_positions) {
        return '';
    }

    const positionsClass = isUpdate ? 'positions-block new-positions' : 'positions-block';

    let positionsHtml = '';
    if (detection.positions && detection.positions.length > 0) {
        const positions = detection.positions.map(position =>
            `<div class="position">${position.player} ${position.name}</div>`
        ).join('');
        positionsHtml = `<div class="${positionsClass}">${positions}</div>`;
    } else {
        positionsHtml = '<div class="no-positions">No position detected</div>';
    }

    return `
        <div class="positions-column">
            <div class="cards-label">Positions:</div>
            <div class="positions-container">
                ${positionsHtml}
            </div>
        </div>
    `;
}

function createMovesSection(detection, isUpdate) {
    if (!config.show_moves) {
        return '';
    }

    if (!detection.moves || detection.moves.length === 0) {
        return `
            <div class="cards-section">
                <div class="cards-label">Moves History:</div>
                <div class="moves-by-street">
                    <div class="no-moves">No moves detected</div>
                </div>
            </div>
        `;
    }

    const movesClass = isUpdate ? 'street-moves-block new-moves' : 'street-moves-block';

    const movesHtml = detection.moves.map(streetData => {
        const moves = streetData.moves.map(move => {
            let moveText = `${move.player_label}: ${move.action}`;
            if (move.amount > 0) {
                moveText += ` $${move.amount}`;
            }
            return `<div class="move">${moveText}</div>`;
        }).join('');

        return `
            <div class="${movesClass}">
                <div class="street-moves-header">${streetData.street}</div>
                <div class="street-moves-list">${moves}</div>
            </div>
        `;
    }).join('');

    return `
        <div class="cards-section">
            <div class="cards-label">Moves History:</div>
            <div class="moves-by-street">
                ${movesHtml}
            </div>
        </div>
    `;
}

function createSolverLinkSection(detection, isUpdate) {
    if (!config.show_solver_link || !detection.solver_link) {
        return '';
    }

    const linkClass = isUpdate ? 'solver-link-block new-solver-link' : 'solver-link-block';

    return `
        <div class="cards-section">
            <div class="cards-label">Solver Analysis !!!BETA!!!:</div>
            <div class="${linkClass}">
                <a href="${detection.solver_link}" target="_blank" class="solver-link">
                    Open in FlopHero 🔗
                </a>
            </div>
        </div>
    `;
}

function createTableContainer(detection, isUpdate, tableId) {
    const tableClass = isUpdate ? 'table-container updated' : 'table-container';

    const tableCardsSection = createTableCardsSection(detection, isUpdate);
    const positionsSection = createPositionsSection(detection, isUpdate);
    const movesSection = createMovesSection(detection, isUpdate);
    const solverLinkSection = createSolverLinkSection(detection, isUpdate);

    // Build main cards section conditionally
    let mainCardsContent = `
        <div class="player-cards-column">
            <div class="cards-label">Player Cards:</div>
            <div class="player-section">
                ${createPlayerCardsSection(detection, isUpdate)}
            </div>
        </div>
    `;

    if (tableCardsSection) {
        mainCardsContent += tableCardsSection;
    }

    if (positionsSection) {
        mainCardsContent += positionsSection;
    }

    const clientId = detection.client_id || 'Unknown';
    const clientLink = detection.client_id ? `/client/${detection.client_id}` : '#';
    const detectionInterval = detection.detection_interval || 3;  // Fallback to 3s

    return `
        <div class="${tableClass}">
            <div class="client-header">
                <div class="client-info">
                    <a href="${clientLink}" class="client-link">
                        <span class="client-id">Client: ${clientId}</span>
                    </a>
                    <div class="table-info">
                        <span class="table-id">Table ${tableId}</span>
                        <span class="window-name-small">${detection.window_name}</span>
                    </div>
                </div>
                <div class="last-update">Updated: ${new Date(detection.last_update).toLocaleTimeString()}</div>
            </div>
            <div class="main-cards-section">
                ${mainCardsContent}
            </div>
            ${movesSection}
            ${solverLinkSection}
        </div>
    `;
}


// Create no clients connected message
function createNoClientsMessage() {
    return `
        <div class="no-clients-container">
            <div class="no-clients-header">
                <div class="no-clients-icon">🔌</div>
                <div class="no-clients-title">No Detection Clients Connected</div>
            </div>
            <div class="no-clients-message">
                <p>Start a detection client to begin monitoring poker tables.</p>
                <div class="no-clients-steps">
                    <div class="step">1. Run detection client on machine with poker tables</div>
                    <div class="step">2. Configure client to connect to this server</div>
                    <div class="step">3. Tables will appear here automatically</div>
                </div>
            </div>
        </div>
    `;
}

function createDynamicTablesGrid(detections) {
    let gridHtml = '<div class="tables-grid">';
    
    // Create containers only for active detections
    detections.forEach((detection, index) => {
        const tableId = (index + 1).toString().padStart(2, '0');
        gridHtml += createTableContainer(detection, false, tableId);
    });
    
    gridHtml += '</div>';
    return gridHtml;
}

function renderCards(detections, isUpdate = false) {
    const content = document.getElementById('content');
    
    // Check if we have any detections from any clients
    const hasDetections = detections && detections.length > 0;
    const hasClientsWithDetections = hasDetections && detections.some(d => d.client_id);
    
    // If no clients are connected, show the no clients message
    if (!hasClientsWithDetections) {
        content.innerHTML = createNoClientsMessage();
        console.log('No clients connected - showing connection message');
        return;
    }
    
    // Create dynamic grid with only active tables
    content.innerHTML = createDynamicTablesGrid(detections);
    
    // Handle update animations
    if (isUpdate) {
        // Add update classes to all table containers
        content.querySelectorAll('.table-container').forEach(container => {
            container.classList.add('updated');
        });
        
        setTimeout(() => {
            document.querySelectorAll('.updated').forEach(el => {
                el.classList.remove('updated');
            });
            document.querySelectorAll('.new-positions').forEach(el => {
                el.classList.remove('new-positions');
            });
            document.querySelectorAll('.new-moves').forEach(el => {
                el.classList.remove('new-moves');
            });
            document.querySelectorAll('.new-cards').forEach(el => {
                el.classList.remove('new-cards');
            });
            document.querySelectorAll('.new-solver-link').forEach(el => {
                el.classList.remove('new-solver-link');
            });
        }, 2000);
    }
    
    // Log detection summary
    console.log(`Rendered ${detections.length} active tables in dynamic grid`);
}

// updateStatus function removed - status element no longer exists

// Global timer display removed - now showing per-client intervals in individual detection blocks

// HTTP Polling system to replace WebSocket
let pollingInterval = null;
let pollingActive = false;
let lastETag = null;

function startPolling() {
    if (pollingActive) {
        return; // Already polling
    }
    
    pollingActive = true;
    updateConnectionStatus('connecting', '🔗 Connecting...');
    
    // Initial poll
    pollForUpdates();
    
    // Start polling every 5 seconds
    pollingInterval = setInterval(() => {
        if (pollingActive) {
            pollForUpdates();
        }
    }, 5000);
    
    console.log('Started HTTP polling (5 second interval)');
}

function stopPolling() {
    pollingActive = false;
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    updateConnectionStatus('disconnected', '🔴 Disconnected');
    console.log('Stopped HTTP polling');
}

async function pollForUpdates() {
    try {
        const headers = {};
        if (lastETag) {
            headers['If-None-Match'] = lastETag;
        }
        
        const response = await fetch('/api/detections', { 
            headers,
            cache: 'no-cache'
        });
        
        if (response.status === 304) {
            // No changes - server returned 304 Not Modified
            updateConnectionStatus('connected', '🟢 Connected (No changes)');
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Update ETag for next request
        lastETag = response.headers.get('ETag');
        
        const data = await response.json();
        
        console.log('Received detection update via polling:', data);
        
        // Check for changes
        const hasChanges = detectChanges(data.detections);
        if (hasChanges) {
            showUpdateIndicator();
        }
        
        // Update UI
        renderCards(data.detections, hasChanges);
        updateClientsNavigation(data.detections);
        previousDetections = data.detections;
        
        updateConnectionStatus('connected', '🟢 Connected');
        
    } catch (error) {
        console.error('Polling error:', error);
        updateConnectionStatus('disconnected', '🔴 Connection Error');
        
        // On error, retry after 10 seconds
        setTimeout(() => {
            if (pollingActive) {
                console.log('Retrying connection...');
            }
        }, 10000);
    }
}

async function loadConfig() {
    try {
        console.log('Loading config from /api/config...');
        const response = await fetch('/api/config');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Server config received:', data);
        
        const oldInterval = config.backend_capture_interval;
        config = data;
        
        console.log(`Config loaded - interval changed from ${oldInterval}s to ${config.backend_capture_interval}s`);
    } catch (error) {
        console.error('Error loading config:', error);
        console.log(`Using fallback config - interval: ${config.backend_capture_interval}s`);
    }
}

async function loadClientsList() {
    try {
        const response = await fetch('/api/clients');
        const data = await response.json();
        
        const clientsNav = document.getElementById('clientsNav');
        const clientCount = document.getElementById('clientCount');
        const clientLinks = document.getElementById('clientLinks');
        
        if (data.connected_clients && data.connected_clients.length > 0) {
            clientCount.textContent = data.connected_clients.length;
            
            const linksHtml = data.connected_clients.map(clientId => 
                `<a href="/client/${clientId}" class="client-nav-link">${clientId}</a>`
            ).join('');
            
            clientLinks.innerHTML = linksHtml;
            clientsNav.style.display = 'block';
        } else {
            clientsNav.style.display = 'none';
        }
        
        console.log('Loaded clients list:', data.connected_clients);
    } catch (error) {
        console.error('Error loading clients list:', error);
    }
}

function updateClientsNavigation(detections) {
    // Extract unique client IDs from detections
    const clientIds = [...new Set(detections.map(d => d.client_id).filter(id => id))];
    
    const clientsNav = document.getElementById('clientsNav');
    const clientCount = document.getElementById('clientCount');
    const clientLinks = document.getElementById('clientLinks');
    
    if (clientIds.length > 0) {
        clientCount.textContent = clientIds.length;
        
        const linksHtml = clientIds.map(clientId => 
            `<a href="/client/${clientId}" class="client-nav-link">${clientId}</a>`
        ).join('');
        
        clientLinks.innerHTML = linksHtml;
        clientsNav.style.display = 'block';
    } else {
        clientsNav.style.display = 'none';
    }
}

// Function removed - no longer needed with HTTP polling
// (incremental updates were a WebSocket optimization)

async function initialize() {
    await loadConfig();
    await loadClientsList();

    console.log('Initializing with HTTP polling...');
    startPolling();
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && !pollingActive) {
        console.log('Page visible again, resuming polling...');
        startPolling();
    } else if (document.hidden && pollingActive) {
        console.log('Page hidden, stopping polling...');
        stopPolling();
    }
});

// Handle page restoration from cache
window.addEventListener('pageshow', function(event) {
    if (event.persisted && !pollingActive) {
        console.log('Page restored from cache, starting polling...');
        startPolling();
    }
});

initialize();
