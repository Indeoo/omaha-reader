let config = {
    backend_capture_interval: 5,
    show_table_cards: true,
    show_positions: true,
    show_moves: true,
    show_solver_link: true
};
let socket = null;
let previousDetections = [];

// Stable table ID management
let tableIdMapping = new Map();
let nextTableId = 1;
const MAX_TABLES = 6;

// Load table ID mapping from localStorage
function loadTableIdMapping() {
    try {
        const stored = localStorage.getItem('tableIdMapping');
        if (stored) {
            const data = JSON.parse(stored);
            tableIdMapping = new Map(Object.entries(data.mapping));
            nextTableId = data.nextId || 1;
        }
    } catch (error) {
        console.warn('Failed to load table ID mapping:', error);
    }
}

// Save table ID mapping to localStorage
function saveTableIdMapping() {
    try {
        const data = {
            mapping: Object.fromEntries(tableIdMapping),
            nextId: nextTableId
        };
        localStorage.setItem('tableIdMapping', JSON.stringify(data));
    } catch (error) {
        console.warn('Failed to save table ID mapping:', error);
    }
}

// Assign stable ID to a detection
function assignStableTableId(detection) {
    const key = `${detection.client_id}_${detection.window_name}`;
    
    if (!tableIdMapping.has(key)) {
        tableIdMapping.set(key, nextTableId.toString().padStart(2, '0'));
        nextTableId++;
        saveTableIdMapping();
    }
    
    return tableIdMapping.get(key);
}

// Clean up old mappings that are no longer active
function cleanupStaleTableMappings(activeDetections) {
    const activeKeys = new Set(activeDetections.map(d => `${d.client_id}_${d.window_name}`));
    let cleaned = false;
    
    for (const [key] of tableIdMapping) {
        if (!activeKeys.has(key)) {
            tableIdMapping.delete(key);
            cleaned = true;
        }
    }
    
    if (cleaned) {
        saveTableIdMapping();
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
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

// Create empty table slot
function createEmptyTableSlot(slotId) {
    return `
        <div class="table-slot empty" id="table-slot-${slotId}">
            <div class="slot-header">
                <div class="slot-label">Table ${slotId}</div>
                <div class="slot-status">No table detected</div>
            </div>
            <div class="slot-content">
                <div class="no-table-message">
                    <div class="no-table-icon">⚫</div>
                    <div class="no-table-text">Waiting for table...</div>
                </div>
            </div>
        </div>
    `;
}

function initializeTablesGrid() {
    const content = document.getElementById('content');
    
    // Create the tables grid container
    let gridHtml = '<div class="tables-grid">';
    
    // Create fixed slots for each table
    for (let i = 1; i <= MAX_TABLES; i++) {
        const slotId = i.toString().padStart(2, '0');
        gridHtml += createEmptyTableSlot(slotId);
    }
    
    gridHtml += '</div>';
    content.innerHTML = gridHtml;
}

function renderCards(detections, isUpdate = false) {
    const content = document.getElementById('content');
    
    // Initialize grid if it doesn't exist
    if (!content.querySelector('.tables-grid')) {
        initializeTablesGrid();
    }
    
    // Clean up old mappings and assign stable IDs
    cleanupStaleTableMappings(detections || []);
    
    // Create mapping of detection to table ID
    const detectionMap = new Map();
    const assignedIds = new Set();
    
    if (detections && detections.length > 0) {
        // Sort detections by assigned ID to maintain consistent ordering
        const sortedDetections = detections.slice().sort((a, b) => {
            const idA = assignStableTableId(a);
            const idB = assignStableTableId(b);
            return idA.localeCompare(idB);
        });
        
        sortedDetections.forEach(detection => {
            const tableId = assignStableTableId(detection);
            detectionMap.set(tableId, detection);
            assignedIds.add(tableId);
        });
    }
    
    // Update each table slot
    for (let i = 1; i <= MAX_TABLES; i++) {
        const slotId = i.toString().padStart(2, '0');
        const slot = document.getElementById(`table-slot-${slotId}`);
        
        if (!slot) continue;
        
        if (detectionMap.has(slotId)) {
            // This slot has an active detection
            const detection = detectionMap.get(slotId);
            const tableHtml = createTableContainer(detection, isUpdate, slotId);
            
            slot.className = `table-slot active ${isUpdate ? 'updated' : ''}`;
            slot.innerHTML = tableHtml;
        } else {
            // This slot is empty
            slot.className = 'table-slot empty';
            slot.innerHTML = `
                <div class="slot-header">
                    <div class="slot-label">Table ${slotId}</div>
                    <div class="slot-status">No table detected</div>
                </div>
                <div class="slot-content">
                    <div class="no-table-message">
                        <div class="no-table-icon">⚫</div>
                        <div class="no-table-text">Waiting for table...</div>
                    </div>
                </div>
            `;
        }
    }
    
    // Handle update animations
    if (isUpdate) {
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
    const activeCount = assignedIds.size;
    console.log(`Rendered ${activeCount}/${MAX_TABLES} tables in fixed positions`);
}

function updateStatus(lastUpdate) {
    const status = document.getElementById('status');
    if (lastUpdate) {
        const date = new Date(lastUpdate);
        status.textContent = `Last update: ${date.toLocaleTimeString()} (Real-time)`;
    }
}

function updateTimerDisplay() {
    document.getElementById('backendInfo').textContent = `every ${config.backend_capture_interval}`;
}

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
        updateStatus(data.last_update);
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
        const response = await fetch('/api/config');
        const data = await response.json();
        config = data;
        updateTimerDisplay();
        console.log('Loaded config:', config);
    } catch (error) {
        console.error('Error loading config:', error);
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
    // Load table ID mapping from localStorage
    loadTableIdMapping();
    
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