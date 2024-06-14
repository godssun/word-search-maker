document.addEventListener("DOMContentLoaded", () => {
  const wordInputsContainer = document.getElementById("wordInputs");

  for (let i = 0; i < 10; i++) {
    const input = document.createElement("input");
    input.type = "text";
    input.id = `word${i + 1}`;
    input.name = `word${i + 1}`;
    input.required = true;
    wordInputsContainer.appendChild(input);
  }
});
