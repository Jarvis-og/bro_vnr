import { RouterProvider, createBrowserRouter } from 'react-router-dom'

import Home from "./pages/Home";
import Assistant from "./pages/Assistant";
import Sidebar from "./components/Sidebar";
import Navigation from "./pages/Navigation";
import AdminPanel from "./pages/AdminPanel";

function App() {

  const router = createBrowserRouter([
    {
      path: "/",
      element: <><Home /> <Sidebar /></>
    },
    {
      path: "/assistant",
      element: <><Assistant /> <Sidebar /></>
    },
    {
      path: "/navigation",
      element: <><Navigation /> <Sidebar /></>
    },
    {
      path: "/admin",
      element: <><AdminPanel /> <Sidebar /></>
    },
  ])

  return (
    <div className="flex h-screen">
      <RouterProvider router={router} />
    </div>
  );
}

export default App;
