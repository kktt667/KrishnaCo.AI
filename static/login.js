document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        
        if (data.success) {
            window.location.href = '/';
        } else {
            alert('Invalid credentials');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during login');
    }
});