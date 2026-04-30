import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";

function VerifyOTP() {
  const [otpCode, setOtpCode] = useState("");
  const [biometricVerified, setBiometricVerified] = useState(false);
  const [message, setMessage] = useState("");

  const navigate = useNavigate();
  const username = localStorage.getItem("username");

  const handleVerify = async (e) => {
    e.preventDefault();

    try {
      const res = await API.post("/verify-otp", {
        username,
        otp_code: otpCode,
        biometric_verified: biometricVerified,
      });

      localStorage.setItem("token", res.data.access_token);
      setMessage(res.data.message);

      navigate("/dashboard");
    } catch (err) {
      setMessage(err.response?.data?.detail || "OTP verification failed");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Verify OTP</h2>

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