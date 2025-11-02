// This file contains JavaScript code for enhancing the functionality of the marketplace, such as handling form submissions or dynamic content updates.

document.addEventListener('DOMContentLoaded', function() {
    const sellForm = document.getElementById('product-sell-form');
    
    if (sellForm) {
        sellForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(sellForm);
            const actionUrl = sellForm.action;

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Product listed successfully!');
                    sellForm.reset();
                } else {
                    alert('Error listing product: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while listing the product.');
            });
        });
    }

    // Additional functionality can be added here
});