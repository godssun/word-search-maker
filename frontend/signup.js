const form = document.querySelector("#signup-form");
const errorMessage = document.querySelector("#error-message");

const checkPassword = () => {
  const formData = new FormData(form);
  const password1 = formData.get("password");
  const password2 = formData.get("password2");

  if (password1 === password2) {
    return true;
  } else {
    errorMessage.textContent = "비밀번호가 다릅니다. 다시 입력해 주세요.";
    errorMessage.style.color = "red";
    return false;
  }
};

const handleSubmit = async (event) => {
  event.preventDefault();
  errorMessage.textContent = ""; // 제출 시 기존 오류 메시지 초기화
  const formData = new FormData(form);
  const sha256Password = sha256(formData.get("password"));
  formData.set("password", sha256Password);

  if (checkPassword()) {
    const res = await fetch("/signup", {
      method: "post",
      body: formData,
    });
    const data = await res.json();

    if (data === "200") {
      alert("회원 가입 성공");
      window.location.pathname = "/login.html";
    }
  }
};

form.addEventListener("submit", handleSubmit);
