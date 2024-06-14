const form = document.querySelector("#login-form");

const handleSubmit = async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const sha256Password = sha256(formData.get("password"));
  formData.set("password", sha256Password);

  try {
    const res = await fetch("/login", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    console.log("Login response:", data); // 응답 확인

    if (data.access_token) {
      localStorage.setItem("token", data.access_token);
      document.getElementById("result").innerText = "Login successful!";
      window.location.pathname = "/";
    } else {
      document.getElementById("result").innerText = "Login failed!";
    }
  } catch (error) {
    console.error("Login error:", error);
    document.getElementById("result").innerText = "Login failed due to an error!";
  }
};

form.addEventListener("submit", handleSubmit);
