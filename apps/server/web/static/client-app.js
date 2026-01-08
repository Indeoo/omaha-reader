let config = {
    backend_capture_interval: 3,  // Updated to match client default  
    show_table_cards: true,
    show_positions: true,
    show_moves: true,
    show_solver_link: true
};
// WebSocket removed - using HTTP polling instead
let previousDetections = [];
let clientId = window.CLIENT_ID;

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

function updateClientStatus(isOnline) {
    const indicator = document.getElementById('statusIndicator');
    const text = document.getElementById('statusText');
    
    if (isOnline) {
        indicator.textContent = '🟢';
        text.textContent = 'Online';
    } else {
        indicator.textContent = '🔴';
        text.textContent = 'Offline';
    }
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

function createTableContainer(detection, isUpdate) {
    const tableClass = isUpdate ? 'table-container updated client-table' : 'table-container client-table';

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

    return `
        <div class="${tableClass}">
            <div class="table-header">
                <div class="table-name">${detection.window_name}</div>
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

function renderCards(detections, isUpdate = false) {
    const content = document.getElementById('content');

    if (!detections || detections.length === 0) {
        content.innerHTML = `<div class="error">No tables detected for client ${clientId}</div>`;
        updateClientStatus(false);
        return;
    }

    updateClientStatus(true);
    
    const html = detections.map(detection =>
        createTableContainer(detection, isUpdate)
    ).join('');

    content.innerHTML = html;

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
}

function updateStatus(lastUpdate, totalTables) {
    const status = document.getElementById('status');
    if (lastUpdate) {
        const date = new Date(lastUpdate);
        const tablesText = totalTables === 1 ? 'table' : 'tables';
        status.textContent = `Last update: ${date.toLocaleTimeString()} - ${totalTables} ${tablesText} (Real-time)`;
    }
}

function updateTimerDisplay() {
    const backendInfoEl = document.getElementById('backendInfo');
    if (backendInfoEl) {
        backendInfoEl.textContent = `every ${config.backend_capture_interval}`;
    }
}

// HTTP Polling system for client-specific data
let pollingInterval = null;
let pollingActive = false;
let lastETag = null;

function startClientPolling() {
    if (pollingActive) {
        return; // Already polling
    }
    
    pollingActive = true;
    updateConnectionStatus('connecting', '🔗 Connecting...');
    
    console.log('Starting HTTP polling for client:', clientId);
    
    // Initial poll
    pollForClientUpdates();
    
    // Start polling every 5 seconds
    pollingInterval = setInterval(() => {
        if (pollingActive) {
            pollForClientUpdates();
        }
    }, 5000);
}

function stopClientPolling() {
    pollingActive = false;
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    updateConnectionStatus('disconnected', '🔴 Disconnected');
    updateClientStatus(false);
    console.log('Stopped HTTP polling for client:', clientId);
}

async function pollForClientUpdates() {
    try {
        const headers = {};
        if (lastETag) {
            headers['If-None-Match'] = lastETag;
        }
        
        const response = await fetch(`/api/client/${clientId}/detections`, { 
            headers,
            cache: 'no-cache'
        });
        
        if (response.status === 304) {
            // No changes - server returned 304 Not Modified
            updateConnectionStatus('connected', '🟢 Connected (No changes)');
            updateClientStatus(true);
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Update ETag for next request
        lastETag = response.headers.get('ETag');
        
        const data = await response.json();
        
        console.log('Received client detection update via polling:', data);
        
        const hasChanges = detectChanges(data.detections);
        if (hasChanges) {
            showUpdateIndicator();
        }

        updateStatus(data.last_update, data.detections.length);
        renderCards(data.detections, hasChanges);
        previousDetections = data.detections;
        
        updateConnectionStatus('connected', '🟢 Connected');
        updateClientStatus(true);
        
    } catch (error) {
        console.error('Client polling error:', error);
        updateConnectionStatus('disconnected', '🔴 Connection Error');
        updateClientStatus(false);
        
        // Check if it's a 404 (client not found)
        if (error.message.includes('404')) {
            document.getElementById('content').innerHTML = `<div class="error">Client ${clientId} not found on server</div>`;
        }
        
        // On error, retry after 10 seconds
        setTimeout(() => {
            if (pollingActive) {
                console.log('Retrying client connection...');
            }
        }, 10000);
    }
}

async function loadConfig() {
    try {
        console.log(`Loading config from /api/client/${clientId}/config...`);
        const response = await fetch(`/api/client/${clientId}/config`);
        
        if (!response.ok) {
            throw new Error(`Client ${clientId} not found (HTTP ${response.status})`);
        }
        
        const data = await response.json();
        console.log('Server client config received:', data);
        
        const oldInterval = config.backend_capture_interval;
        config = data;
        updateTimerDisplay();
        
        console.log(`Client config loaded - interval changed from ${oldInterval}s to ${config.backend_capture_interval}s`);
    } catch (error) {
        console.error('Error loading client config:', error);
        console.log(`Using fallback config - interval: ${config.backend_capture_interval}s`);
        document.getElementById('content').innerHTML = `<div class="error">Error: ${error.message}</div>`;
        updateConnectionStatus('disconnected', '🔴 Client Not Found');
        updateTimerDisplay();  // Still show timer with fallback
    }
}

async function loadInitialData() {
    try {
        const response = await fetch(`/api/client/${clientId}/data`);
        if (response.ok) {
            const data = await response.json();
            console.log('Loaded initial client data:', data);
            updateStatus(data.last_update, data.detections.length);
            renderCards(data.detections, false);
            previousDetections = data.detections;
        }
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

async function initialize() {
    if (!clientId) {
        document.getElementById('content').innerHTML = '<div class="error">No client ID specified</div>';
        return;
    }

    await loadConfig();
    await loadInitialData();

    console.log('Initializing with HTTP polling for client:', clientId);
    startClientPolling();
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && !pollingActive) {
        console.log('Page visible again, resuming client polling...');
        startClientPolling();
    } else if (document.hidden && pollingActive) {
        console.log('Page hidden, stopping client polling...');
        stopClientPolling();
    }
});

// Handle page restoration from cache
window.addEventListener('pageshow', function(event) {
    if (event.persisted && !pollingActive) {
        console.log('Page restored from cache, starting client polling...');
        startClientPolling();
    }
});

// Clean up polling on page unload
window.addEventListener('beforeunload', function() {
    if (pollingActive) {
        stopClientPolling();
    }
});

initialize();
