# HospitAI Frontend

React-based dashboard for the HospitAI hospital surge prediction system.

## Tech Stack

- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- shadcn/ui component library
- Recharts for data visualization
- React Query for data fetching

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── contexts/       # React context providers
├── hooks/          # Custom React hooks
├── lib/            # Utility functions
├── pages/          # Page components
└── main.tsx        # Application entry point
```

## API Integration

The frontend connects to the FastAPI backend at the URL specified in `VITE_API_URL`. Key endpoints:

- `/api/dashboard/summary` - Dashboard metrics
- `/api/predictions` - ML predictions
- `/api/agent/run` - AI agent analysis
- `/api/upload` - Data upload

## Deployment

Build the production bundle:

```bash
npm run build
```

The output will be in the `dist/` directory, ready for static hosting.
