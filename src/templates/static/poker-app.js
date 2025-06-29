let config = {
    backend_capture_interval: 5
};
let eventSource = null;
let previousDetections = [];

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
        <div class="cards-label">Table Cards: ${streetDisplay}</div>
        <div class="cards-container">${cardsHtml}</div>
    `;
}

function createPositionsSection(detection, isUpdate) {
    const positionsClass = isUpdate ? 'positions-block new-positions' : 'positions-block';

    if (detection.positions && detection.positions.length > 0) {
        const positionsHtml = detection.positions.map(position =>
            `<div class="position">${position.player} ${position.name}</div>`
        ).join('');

        return `<div class="${positionsClass}">${positionsHtml}</div>`;
    }

    return '<div class="no-positions">No position detected</div>';
}

function createMovesSection(detection, isUpdate) {
    if (!detection.moves || detection.moves.length === 0) {
        return '<div class="no-moves">No moves detected</div>';
    }

    const movesClass = isUpdate ? 'street-moves-block new-moves' : 'street-moves-block';

    return detection.moves.map(streetData => {
        const movesHtml = streetData.moves.map(move => {
            let moveText = `${move.player_label}: ${move.action}`;
            if (move.amount > 0) {
                moveText += ` $${move.amount}`;
            }
            return `<div class="move">${moveText}</div>`;
        }).join('');

        return `
            <div class="${movesClass}">
                <div class="street-moves-header">${streetData.street}</div>
                <div class="street-moves-list">${movesHtml}</div>
            </div>
        `;
    }).join('');
}

function createTableContainer(detection, isUpdate) {
    const tableClass = isUpdate ? 'table-container updated' : 'table-container';

    return `
        <div class="${tableClass}">
            <div class="table-name">${detection.window_name}</div>
            <div class="main-cards-section">
                <div class="player-cards-column">
                    <div class="cards-label">Player Cards:</div>
                    <div class="player-section">
                        ${createPlayerCardsSection(detection, isUpdate)}
                    </div>
                </div>
                <div class="table-cards-column">
                    ${createTableCardsSection(detection, isUpdate)}
                </div>
                <div class="positions-column">
                    <div class="cards-label">Positions:</div>
                    <div class="positions-container">
                        ${createPositionsSection(detection, isUpdate)}
                    </div>
                </div>
            </div>
            <div class="cards-section">
                <div class="cards-label">Moves History:</div>
                <div class="moves-by-street">
                    ${createMovesSection(detection, isUpdate)}
                </div>
            </div>
        </div>
    `;
}

function renderCards(detections, isUpdate = false) {
    const content = document.getElementById('content');

    if (!detections || detections.length === 0) {
        content.innerHTML = '<div class="error">No tables detected</div>';
        return;
    }

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
        }, 2000);
    }
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

function initializeSSE() {
    if (eventSource) {
        eventSource.close();
    }

    updateConnectionStatus('connecting', '🔗 Connecting...');

    eventSource = new EventSource('/api/stream');

    eventSource.onopen = function(event) {
        console.log('SSE connection opened');
        updateConnectionStatus('connected', '🟢 Connected');
    };

    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);

            switch(data.type) {
                case 'connected':
                    console.log('SSE client connected:', data.client_id);
                    break;

                case 'detection_update':
                    console.log('Received detection update:', data);

                    const hasChanges = detectChanges(data.detections);
                    if (hasChanges) {
                        showUpdateIndicator();
                    }

                    updateStatus(data.last_update);
                    renderCards(data.detections, hasChanges);
                    previousDetections = data.detections;
                    break;

                case 'heartbeat':
                    break;

                default:
                    console.log('Unknown SSE message type:', data.type);
            }
        } catch (e) {
            console.error('Error parsing SSE message:', e);
        }
    };

    eventSource.onerror = function(event) {
        console.error('SSE connection error:', event);
        updateConnectionStatus('disconnected', '🔴 Disconnected');

        setTimeout(() => {
            if (eventSource.readyState === EventSource.CLOSED) {
                console.log('Attempting to reconnect SSE...');
                initializeSSE();
            }
        }, 3000);
    };
}

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        config = data;
        updateTimerDisplay();
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

async function initialize() {
    await loadConfig();

    if (typeof(EventSource) !== "undefined") {
        console.log('Initializing with SSE...');
        initializeSSE();
    } else {
        console.error('SSE not supported by this browser');
        document.getElementById('content').innerHTML = '<div class="error">Real-time updates not supported by this browser</div>';
        updateConnectionStatus('disconnected', '🔴 Not Supported');
    }
}

document.addEventListener('visibilitychange', function() {
    if (!document.hidden && eventSource && eventSource.readyState === EventSource.CLOSED) {
        console.log('Page visible again, reconnecting SSE...');
        initializeSSE();
    }
});

window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        console.log('Page restored from cache, reconnecting SSE...');
        initializeSSE();
    }
});

initialize();