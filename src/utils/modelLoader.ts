// Character models mapping
export const CHARACTER_MODELS = {
  analyst: {
    model: '/assets/kenney_blocky-characters/Models/advancedCharacter.fbx',
    skin: 'blue',
    accessories: ['laptop', 'glasses'],
  },
  quant: {
    model: '/assets/kenney_blocky-characters/Models/advancedCharacter.fbx',
    skin: 'green',
    accessories: ['tablet', 'calculator'],
  },
  executive: {
    model: '/assets/kenney_blocky-characters/Models/advancedCharacter.fbx',
    skin: 'orange',
    accessories: ['phone', 'tie'],
  },
  riskManager: {
    model: '/assets/kenney_blocky-characters/Models/advancedCharacter.fbx',
    skin: 'red',
    accessories: ['clipboard', 'badge'],
  },
};

// Furniture models mapping by room type
export const FURNITURE_MODELS = {
  // Central area furniture for better immersion
  centralArea: [
    { name: 'receptionDesk', model: '/assets/kenney_furniture-kit/Models/GLTF format/tableRound.glb', positions: [[0, 0, 0]], scale: 4 },
    { name: 'receptionChairs', model: '/assets/kenney_furniture-kit/Models/GLTF format/loungeDesignChair.glb', positions: [[2, 0, 2], [-2, 0, 2], [2, 0, -2], [-2, 0, -2]], scale: 2 },
    { name: 'centralDisplays', model: '/assets/kenney_furniture-kit/Models/GLTF format/televisionModern.glb', positions: [[0, 1.5, -5], [5, 1.5, 0], [0, 1.5, 5], [-5, 1.5, 0]], scale: 3, rotation: [0, Math.PI/2, 0] },
    { name: 'centralPlants', model: '/assets/kenney_furniture-kit/Models/GLTF format/pottedPlant.glb', positions: [[4, 0, 4], [-4, 0, -4], [4, 0, -4], [-4, 0, 4]], scale: 3 },
    { name: 'centralRugs', model: '/assets/kenney_furniture-kit/Models/GLTF format/rugRound.glb', positions: [[0, 0.01, 0]], scale: 5 },
    { name: 'tradingTerminals', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerScreen.glb', positions: [[1, 0.25, 0], [-1, 0.25, 0], [0, 0.25, 1], [0, 0.25, -1]], scale: 1.5, rotation: [0, Math.PI/4, 0] },
    { name: 'centralLighting', model: '/assets/kenney_furniture-kit/Models/GLTF format/lampSquareCeiling.glb', positions: [[0, 2.5, 0]], scale: 3 },
  ],
  
  fundamentalAnalysis: [
    { name: 'desk', model: '/assets/kenney_furniture-kit/Models/GLTF format/desk.glb', positions: [[-2, 0, -2], [2, 0, -2], [-2, 0, 2], [2, 0, 2]], scale: 2 },
    { name: 'chair', model: '/assets/kenney_furniture-kit/Models/GLTF format/chairModernFrameCushion.glb', positions: [[-2, 0, -1.4], [2, 0, -1.4], [-2, 0, 2.6], [2, 0, 2.6]], scale: 2, rotation: [0, Math.PI, 0] },
    { name: 'computer', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerScreen.glb', positions: [[-2, 0.25, -2], [2, 0.25, -2], [-2, 0.25, 2], [2, 0.25, 2]], scale: 2 },
    { name: 'keyboard', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerKeyboard.glb', positions: [[-2, 0.25, -1.5], [2, 0.25, -1.5], [-2, 0.25, 2.5], [2, 0.25, 2.5]], scale: 2 },
    { name: 'plant', model: '/assets/kenney_furniture-kit/Models/GLTF format/plantSmall3.glb', positions: [[0, 0, 0], [3, 0, 3]], scale: 2 },
    { name: 'bookcase', model: '/assets/kenney_furniture-kit/Models/GLTF format/bookcaseClosedWide.glb', positions: [[0, 0, -3]], scale: 2 },
    { name: 'rug', model: '/assets/kenney_furniture-kit/Models/GLTF format/rugRectangle.glb', positions: [[0, 0.01, 0]], scale: 4 },
    { name: 'booksRow', model: '/assets/kenney_furniture-kit/Models/GLTF format/books.glb', positions: [[-0.5, 0.25, -3], [0.5, 0.25, -3]], scale: 2 },
  ],
  technicalAnalysis: [
    { name: 'deskLarge', model: '/assets/kenney_furniture-kit/Models/GLTF format/tableCross.glb', positions: [[0, 0, 0]], scale: 4 },
    { name: 'chair', model: '/assets/kenney_furniture-kit/Models/GLTF format/chairModernCushion.glb', positions: [[-1.5, 0, -1], [0, 0, -1], [1.5, 0, -1], [-1.5, 0, 1], [0, 0, 1], [1.5, 0, 1]], scale: 2, rotation: [0, Math.PI, 0] },
    { name: 'monitor', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerScreen.glb', positions: [[-1.5, 0.25, -0.5], [0, 0.25, -0.5], [1.5, 0.25, -0.5], [-1.5, 0.25, 0.5], [0, 0.25, 0.5], [1.5, 0.25, 0.5]], scale: 2 },
    { name: 'keyboard', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerKeyboard.glb', positions: [[-1.5, 0.25, 0], [0, 0.25, 0], [1.5, 0.25, 0], [-1.5, 0.25, 1], [0, 0.25, 1], [1.5, 0.25, 1]], scale: 2 },
    { name: 'wallDisplay', model: '/assets/kenney_furniture-kit/Models/GLTF format/televisionModern.glb', positions: [[0, 1, -3], [-2, 1, -3], [2, 1, -3]], scale: 2.5, rotation: [0, 0, 0] },
    { name: 'rug', model: '/assets/kenney_furniture-kit/Models/GLTF format/rugRectangle.glb', positions: [[0, 0.01, 0]], scale: 4 },
  ],
  executiveSuite: [
    { name: 'deskExecutive', model: '/assets/kenney_furniture-kit/Models/GLTF format/tableCrossCloth.glb', positions: [[0, 0, 2]], scale: 3 },
    { name: 'chairExecutive', model: '/assets/kenney_furniture-kit/Models/GLTF format/loungeChair.glb', positions: [[0, 0, 3]], scale: 2, rotation: [0, Math.PI, 0] },
    { name: 'computerExecutive', model: '/assets/kenney_furniture-kit/Models/GLTF format/laptop.glb', positions: [[0, 0.25, 2]], scale: 2 },
    { name: 'conferenceTable', model: '/assets/kenney_furniture-kit/Models/GLTF format/tableRound.glb', positions: [[0, 0, -1.5]], scale: 3 },
    { name: 'conferenceChairs', model: '/assets/kenney_furniture-kit/Models/GLTF format/chairRounded.glb', positions: [[0, 0, -0.5], [0, 0, -2.5], [-1, 0, -1.5], [1, 0, -1.5]], scale: 2 },
    { name: 'plant', model: '/assets/kenney_furniture-kit/Models/GLTF format/plantSmall1.glb', positions: [[-3, 0, -3], [3, 0, -3]], scale: 3 },
    { name: 'cabinetFiles', model: '/assets/kenney_furniture-kit/Models/GLTF format/cabinetTelevision.glb', positions: [[-3, 0, 3]], scale: 2.5 },
    { name: 'executiveRug', model: '/assets/kenney_furniture-kit/Models/GLTF format/rugRounded.glb', positions: [[0, 0.01, 0]], scale: 5 },
    { name: 'wallArt', model: '/assets/kenney_furniture-kit/Models/GLTF format/kitchenBar.glb', positions: [[3, 1.5, -3]], scale: 2, rotation: [0, 0, Math.PI/2] },
  ],
  tradingFloor: [
    { name: 'deskRow1', model: '/assets/kenney_furniture-kit/Models/GLTF format/benchCushion.glb', positions: [[0, 0, -2]], scale: 4, rotation: [0, Math.PI/2, 0] },
    { name: 'deskRow2', model: '/assets/kenney_furniture-kit/Models/GLTF format/benchCushion.glb', positions: [[0, 0, 0]], scale: 4, rotation: [0, Math.PI/2, 0] },
    { name: 'deskRow3', model: '/assets/kenney_furniture-kit/Models/GLTF format/benchCushion.glb', positions: [[0, 0, 2]], scale: 4, rotation: [0, Math.PI/2, 0] },
    { name: 'chairRow1', model: '/assets/kenney_furniture-kit/Models/GLTF format/chairDesk.glb', positions: [[-1.5, 0, -2], [0, 0, -2], [1.5, 0, -2]], scale: 2, rotation: [0, Math.PI, 0] },
    { name: 'chairRow2', model: '/assets/kenney_furniture-kit/Models/GLTF format/chairDesk.glb', positions: [[-1.5, 0, 0], [0, 0, 0], [1.5, 0, 0]], scale: 2, rotation: [0, Math.PI, 0] },
    { name: 'chairRow3', model: '/assets/kenney_furniture-kit/Models/GLTF format/chairDesk.glb', positions: [[-1.5, 0, 2], [0, 0, 2], [1.5, 0, 2]], scale: 2, rotation: [0, Math.PI, 0] },
    { name: 'computerRow1', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerScreen.glb', positions: [[-1.5, 0.25, -2], [0, 0.25, -2], [1.5, 0.25, -2]], scale: 2 },
    { name: 'computerRow2', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerScreen.glb', positions: [[-1.5, 0.25, 0], [0, 0.25, 0], [1.5, 0.25, 0]], scale: 2 },
    { name: 'computerRow3', model: '/assets/kenney_furniture-kit/Models/GLTF format/computerScreen.glb', positions: [[-1.5, 0.25, 2], [0, 0.25, 2], [1.5, 0.25, 2]], scale: 2 },
    { name: 'wallScreens', model: '/assets/kenney_furniture-kit/Models/GLTF format/televisionModern.glb', positions: [[-1.5, 1.5, -3], [0, 1.5, -3], [1.5, 1.5, -3]], scale: 2.5, rotation: [0, 0, 0] },
    { name: 'tradingRug', model: '/assets/kenney_furniture-kit/Models/GLTF format/rugRectangle.glb', positions: [[0, 0.01, 0]], scale: 5 },
  ],
};

// Room colors - using a more vibrant professional palette for better visual distinction
export const ROOM_COLORS = {
  fundamentalAnalysis: '#1976d2', // Richer blue
  technicalAnalysis: '#2e7d32',   // Richer green
  executiveSuite: '#e65100',      // Richer orange
  tradingFloor: '#d32f2f',        // Richer red
};

// Floor colors - improved for better visual contrast
export const FLOOR_COLOR = '#5d4037';       // Darker rich brown for better floor contrast
export const CORRIDOR_COLOR = '#8d6e63';    // Medium brown for corridors
export const GRASS_COLOR = '#7cb342';       // Richer green for outdoor areas

// Character Colors - enhanced for better visibility and distinction
export const CHARACTER_COLORS = {
  analyst: '#03a9f4',
  quant: '#00c853',
  executive: '#ff9100',
  riskManager: '#ff1744',
};

// Market data colors
export const MARKET_DATA_COLORS = {
  bullish: '#4caf50',   // Green
  bearish: '#f44336',   // Red
  neutral: '#2196f3',   // Blue
  alert: '#ff9800',     // Orange
  background: '#263238' // Dark blue-grey
};