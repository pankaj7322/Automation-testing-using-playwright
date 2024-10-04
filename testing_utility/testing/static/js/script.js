document.addEventListener('DOMContentLoaded', function() {
  const addMoreButton = document.getElementById('add-more');
  const linkInputsDiv = document.getElementById('link-inputs');

  addMoreButton.addEventListener('click', function() {
      const inputGroup = document.createElement('div');
      inputGroup.classList.add('input-group1');

      const inputNumber = document.createElement('span');
      inputNumber.classList.add('input-number');
      inputNumber.textContent = `${linkInputsDiv.children.length + 1}.`;

      const urlInput = document.createElement('input');
      urlInput.setAttribute('type', 'url');
      urlInput.setAttribute('name', 'url[]');
      urlInput.setAttribute('placeholder', 'Enter link');
      urlInput.required = true;

      const usernameInput = document.createElement('input');
      usernameInput.setAttribute('type', 'text');
      usernameInput.setAttribute('name', 'username[]');
      usernameInput.setAttribute('placeholder', 'Enter username');
      usernameInput.required = true;

      const passwordInput = document.createElement('input');
      passwordInput.setAttribute('type', 'password');
      passwordInput.setAttribute('name', 'password[]');
      passwordInput.setAttribute('placeholder', 'Enter password');
      passwordInput.required = true;

      // Create a Delete button
      const deleteButton = document.createElement('button');
      deleteButton.setAttribute('type', 'button');
      deleteButton.classList.add('delete-btn');
      deleteButton.textContent = '-';

      // Attach event listener to the Delete button
      deleteButton.addEventListener('click', function() {
          inputGroup.remove(); // Remove the input group from the DOM
          updateInputNumbers(); // Update the numbers
      });

      inputGroup.appendChild(inputNumber);
      inputGroup.appendChild(urlInput);
      inputGroup.appendChild(usernameInput);
      inputGroup.appendChild(passwordInput);
      inputGroup.appendChild(deleteButton); // Add the Delete button to the input group

      linkInputsDiv.appendChild(inputGroup);
      updateInputNumbers(); // Update input numbers after adding a new input group
  });

  function updateInputNumbers() {
      const inputGroups = linkInputsDiv.children;
      for (let i = 0; i < inputGroups.length; i++) {
          const inputNumber = inputGroups[i].querySelector('.input-number');
          inputNumber.textContent = `${i + 1}.`; // Update input number
      }
  }
});
