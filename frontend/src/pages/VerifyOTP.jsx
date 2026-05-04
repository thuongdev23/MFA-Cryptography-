import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";

function VerifyOTP() {
  const [otpCode, setOtpCode] = useState("");
  const [biometricVerified, setBiometricVerified] = useState(false);
  const [message, setMessage] = useState("");

  const navigate = useNavigate();

  const email = localStorage.getItem("email");
  const qrCode = localStorage.getItem("qr_code");

  const handleVerify = async (e) => {
    e.preventDefault();

    const payload = {
      email: email,
      otp_code: otpCode,
      biometric_verified: biometricVerified,
    };

    console.log("Sending OTP payload:", payload);

    try {
      const res = await API.post("/verify-otp", payload);

      localStorage.setItem("token", res.data.access_token);
      setMessage(res.data.message);

      navigate("/dashboard");
    } catch (err) {
      console.log("OTP error:", err.response?.data);

      const detail = err.response?.data?.detail;

      if (Array.isArray(detail)) {
        setMessage(detail[0]?.msg || "OTP verification failed");
      } else {
        setMessage(detail || "OTP verification failed");
      }
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Verify OTP</h2>

      {qrCode && (
        <div>
          <h3>Scan QR Code</h3>
          <img src={qrCode} alt="OTP QR Code" width="220" />
        </div>
      )}

      <form onSubmit={handleVerify}>
        <input
          type="text"
          placeholder="Enter 6-digit OTP"
          value={otpCode}
          onChange={(e) => setOtpCode(e.target.value)}
        />

        <br /><br />

        <label>
          <input
            type="checkbox"
            checked={biometricVerified}
            onChange={(e) => setBiometricVerified(e.target.checked)}
          />
          Simulated biometric verification
        </label>

        <br /><br />

        <button type="submit">Verify MFA</button>
      </form>

      <p>{message}</p>
    </div>
  );
}

export default VerifyOTP;