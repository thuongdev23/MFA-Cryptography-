import { useState } from "react";
import API from "../api";

function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [qrCode, setQrCode] = useState("");
  const [message, setMessage] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();

    try {
      const res = await API.post("/register", {
        email,
        password,
      });

      setMessage(res.data.message);
      setQrCode(res.data.qr_code);
    } catch (err) {
      setMessage(err.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Register</h2>

      <form onSubmit={handleRegister}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <br /><br />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <br /><br />

        <button type="submit">Register</button>
      </form>

      <p>{message}</p>

      {qrCode && (
        <div>
          <h3>Scan this QR code with Google Authenticator</h3>
          <img src={qrCode} alt="OTP QR Code" width="220" />
        </div>
      )}
    </div>
  );
}

export default Register;