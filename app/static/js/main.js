// Funções utilitárias
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Validação de formulários
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Manipulação de documentos
function confirmDelete(event) {
    if (!confirm('Tem certeza que deseja excluir este item?')) {
        event.preventDefault();
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Adiciona validação a todos os formulários
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(this)) {
                event.preventDefault();
                showAlert('Por favor, preencha todos os campos obrigatórios.', 'danger');
            }
        });
    });
    
    // Adiciona confirmação para botões de exclusão
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', confirmDelete);
    });
}); 