import { useEffect, useState } from "react";
import API from "../api";

function Dashboard() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");

    API.get("/dashboard", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        setMessage(res.data.message);
      })
      .catch((err) => {
        setMessage(err.response?.data?.detail || "Access denied");
      });
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>Protected Dashboard</h2>
      <p>{message}</p>
    </div>
  );
}

export default Dashboard;