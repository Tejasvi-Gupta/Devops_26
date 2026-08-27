import { useState } from "react";
import Shell from "./components/Shell";
import InstructorPage from "./pages/InstructorPage";
import StudentPage from "./pages/StudentPage";

export default function App() {
  const [view, setView] = useState("instructor");

  return (
    <Shell view={view} onChangeView={setView}>
      {view === "instructor" ? <InstructorPage /> : <StudentPage />}
    </Shell>
  );
}
