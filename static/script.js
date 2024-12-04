function openSidebar() {
  document.querySelector('.sidebar').classList.add('open');
}

function closeSidebar() {
  document.querySelector('.sidebar').classList.remove('open');
}

// Додаємо обробник для кнопки меню, якщо вона існує
const menuButton = document.querySelector('.menu-button');
if (menuButton) {
  menuButton.addEventListener('click', openSidebar);
}

function deleteOption(pollId) {
  if (confirm("Ви впевнені, що хочете видалити це голосування?")) {
    fetch(`/delete_poll/${pollId}`, { method: 'POST' })
      .then((response) => {
        if (response.ok) {
          alert("Голосування успішно видалено");
          location.reload(); // Перезавантаження сторінки
        } else {
          alert("Помилка при видаленні голосування");
        }
      })
      .catch((error) => {
        console.error("Помилка:", error);
        alert("Не вдалося виконати запит.");
      });
  }
}
