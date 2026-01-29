function el(id) {
  return document.getElementById(id);
}

function renderTasks(tasks) {
  const list = el("taskList");
  list.innerHTML = "";

  tasks.forEach((t) => {
    const li = document.createElement("li");
    li.className = "task-item";

    const text = document.createElement("span");
    text.innerText = t.task;

    const right = document.createElement("div");
    right.className = "task-right";

    const time = document.createElement("small");
    time.className = "muted";
    time.innerText = t.created_at ? `(${t.created_at})` : "";

    const delBtn = document.createElement("button");
    delBtn.className = "icon-btn";
    delBtn.title = "Delete";

    // Using an icon file (optional). If you don't have it yet, the button still works.
    const icon = document.createElement("img");
    icon.src = "/static/icons/trash.svg";
    icon.alt = "Delete";
    icon.width = 16;
    icon.height = 16;

    delBtn.appendChild(icon);
    delBtn.onclick = () => deleteTask(t.id);

    right.appendChild(time);
    right.appendChild(delBtn);

    li.appendChild(text);
    li.appendChild(right);

    list.appendChild(li);
  });
}

function loadTasks() {
  fetch("/api/tasks")
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        console.error(data.error);
        return;
      }
      renderTasks(data);
    })
    .catch((err) => console.error("Load tasks error:", err));
}

function addTask() {
  const task = (el("taskInput").value || "").trim();
  if (!task) return;

  fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }
      el("taskInput").value = "";
      loadTasks();
    })
    .catch((err) => console.error("Add task error:", err));
}

function deleteTask(id) {
  fetch(`/api/tasks/${id}`, { method: "DELETE" })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }
      loadTasks();
    })
    .catch((err) => console.error("Delete task error:", err));
}

// Wire up button + enter key
document.addEventListener("DOMContentLoaded", () => {
  const addBtn = el("addBtn");
  const input = el("taskInput");

  addBtn.addEventListener("click", addTask);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") addTask();
  });

  loadTasks();
});
