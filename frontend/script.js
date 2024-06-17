document.addEventListener("DOMContentLoaded", function () {
  var wordForm = document.getElementById("wordForm");
  if (wordForm) {
    wordForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const title = document.getElementById("title").value.toUpperCase();
      const description = document.getElementById("description").value.toUpperCase();
      const words = document
        .getElementById("words")
        .value.split(",")
        .map((word) => word.trim().toUpperCase());

      // if (words.length < 10) {
      //   alert("Please enter at least 10 words.");
      //   return;
      // }

      try {
        const response = await fetch("/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description, words }),
        });

        if (!response.ok) {
          const errorDetail = await response.json();
          console.error("Error:", errorDetail.detail);
          alert(`Error: ${errorDetail.detail}`);
          return;
        }

        const data = await response.json();
        const link = document.getElementById("link");
        link.innerHTML = `<a href="game.html?gameId=${data.gameId}">Play Game</a>`;
      } catch (error) {
        console.error("Unexpected error:", error);
        alert("An unexpected error occurred");
      }
    });
  }

  const urlParams = new URLSearchParams(window.location.search);
  const gameId = urlParams.get("gameId");

  if (gameId) {
    const startButton = document.getElementById("start-button");
    const usernameInput = document.getElementById("username");

    startButton.addEventListener("click", function () {
      const username = usernameInput.value.trim();
      if (username) {
        startGame(gameId, username);
      } else {
        alert("Please enter your name.");
      }
    });
  }

  async function startGame(gameId, username) {
    try {
      const response = await fetch(`/game/${gameId}`);
      const data = await response.json();

      if (!data || !Array.isArray(data.grid) || !Array.isArray(data.words)) {
        console.error("Invalid game data:", data);
        alert("Error: Invalid game data received.");
        return;
      }

      document.getElementById("game-title").textContent = data.title || "UNKNOWN TITLE";
      document.getElementById("game-description").textContent = data.description || "NO DESCRIPTION";
      document.getElementById("user-input").style.display = "none";

      const grid = document.getElementById("grid");
      grid.innerHTML = "";

      const wordList = document.getElementById("words");
      wordList.innerHTML = "";
      data.words.forEach((word) => {
        const wordItem = document.createElement("li");
        wordItem.textContent = word.toUpperCase();
        wordItem.id = `word-${word}`;
        wordList.appendChild(wordItem);
      });

      const cells = [];
      data.grid.forEach((row, rowIndex) => {
        row.forEach((cell, colIndex) => {
          const cellDiv = document.createElement("div");
          cellDiv.textContent = cell.toUpperCase();
          cellDiv.dataset.row = rowIndex;
          cellDiv.dataset.col = colIndex;
          cellDiv.addEventListener("mousedown", startDrag);
          cellDiv.addEventListener("mouseenter", drag);
          cellDiv.addEventListener("mouseup", endDrag);
          grid.appendChild(cellDiv);
          cells.push(cellDiv);
        });
      });

      let startTime = Date.now();
      let timerInterval = setInterval(() => {
        const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById("time").textContent = `Time elapsed: ${elapsedTime}s`;
      }, 1000);

      function checkWord(selectedWord, words) {
        if (words.includes(selectedWord)) {
          selectedCells.forEach((cell) => cell.classList.add("correct"));
          words.splice(words.indexOf(selectedWord), 1);
          updateWordList(words);
          if (words.length === 0) {
            clearInterval(timerInterval);
            const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
            const points = calculatePoints(elapsedTime);
            submitScore(gameId, username, points, elapsedTime);
          }
        } else {
          selectedCells.forEach((cell) => cell.classList.add("incorrect"));
          setTimeout(() => {
            selectedCells.forEach((cell) => cell.classList.remove("incorrect"));
          }, 1000);
        }
      }

      function updateWordList(words) {
        const wordList = document.getElementById("words");
        wordList.childNodes.forEach((wordItem) => {
          if (!words.includes(wordItem.textContent)) {
            wordItem.classList.add("found");
          }
        });
      }

      function calculatePoints(elapsedTime) {
        const basePoints = 1000;
        return basePoints - elapsedTime;
      }

      async function submitScore(gameId, username, points, timeElapsed) {
        try {
          const response = await fetch("/score", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ gameId, username, points, timeElapsed }),
          });

          if (response.ok) {
            const data = await response.json();
            alert("Congratulations! You've found all the words.");
            updateLeaderboard(data.scores);
          } else {
            alert("Failed to submit score.");
          }
        } catch (error) {
          console.error("Error submitting score:", error);
        }
      }

      function updateLeaderboard(scores) {
        const scoresElement = document.getElementById("scores");
        scoresElement.innerHTML = "";
        scores.forEach((score, index) => {
          const scoreItem = document.createElement("li");
          scoreItem.textContent = `${score.username}: ${score.points}`;
          if (index < 3) {
            scoreItem.style.fontWeight = "bold";
          }
          scoresElement.appendChild(scoreItem);
        });
      }

      let isDragging = false;
      let selectedCells = [];

      function startDrag(event) {
        isDragging = true;
        selectedCells = [event.target];
        event.target.classList.add("selected");
      }

      function drag(event) {
        if (isDragging && !selectedCells.includes(event.target)) {
          selectedCells.push(event.target);
          event.target.classList.add("selected");
        }
      }

      function endDrag(event) {
        isDragging = false;
        const selectedWord = selectedCells.map((cell) => cell.textContent).join("");
        checkWord(selectedWord, data.words);
        selectedCells.forEach((cell) => cell.classList.remove("selected"));
        selectedCells = [];
      }
    } catch (error) {
      console.error("Error fetching game data:", error);
      alert("Error: Unable to fetch game data.");
    }
  }
});
