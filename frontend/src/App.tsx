import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ToastProvider } from "./components/ui/Toast";
import { TripList } from "./pages/TripList";
import { TripEditor } from "./pages/TripEditor";

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<TripList />} />
          <Route path="/trips/:id" element={<TripEditor />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}
