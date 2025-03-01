# AI Hedge Fund Simulation

A 3D web-based simulation that visualizes an AI-driven hedge fund operation in a Crossy Road-inspired isometric style. The simulation displays different departments with AI entities moving between rooms, interacting with each other, and making investment decisions that impact fund performance metrics.

## Features

- Isometric 3D view of a hedge fund office with multiple specialized rooms
- AI-driven characters that autonomously move, interact, and make decisions
- Activity logging system to track all agent behaviors
- Performance metrics visualization for fund performance
- Day/night cycle and dynamic market events
- Character focus mode and room focus mode
- Speech bubbles for character conversations

## Technology Stack

- **Frontend Framework**: React with TypeScript
- **3D Rendering**: Three.js with react-three-fiber and drei
- **State Management**: Redux with Redux Toolkit
- **UI Components**: Custom styled components
- **Animation**: Custom animation system for characters

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-hedge-fund-simulation.git
cd ai-hedge-fund-simulation
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Start the development server:
```bash
npm start
# or
yarn start
```

4. Open your browser and navigate to `http://localhost:3000`

## Usage

- **Camera Controls**: Use the mouse to orbit around the scene (when no entity is focused)
- **Character Interaction**: Click on a character to focus and see detailed information
- **Room Interaction**: Click on a room to focus on it
- **Activity Log**: View all activities in the right panel, with filtering options
- **Simulation Controls**: Start/pause the simulation and adjust speed using the controls at the bottom

## Project Structure

- `/src/components`: React components for UI elements
- `/src/store`: Redux store configuration and slices for state management
- `/src/hooks`: Custom hooks including the simulation engine
- `/src/scenes`: 3D scene components for the environment
- `/src/models`: TypeScript interfaces and types
- `/src/utils`: Utility functions and helpers

## Simulated AI Behavior

The hedge fund simulation features different types of AI-driven characters:

- **Analysts**: Focus on fundamental analysis of companies and markets
- **Quants**: Specialize in quantitative models and algorithms
- **Executives**: Make high-level decisions and define strategy
- **Risk Managers**: Monitor and mitigate various types of financial risks

Each character type has different skills, behaviors, and decision-making processes that influence the fund's performance over time.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the isometric style of Crossy Road
- Built for educational purposes to visualize AI-driven financial decision making