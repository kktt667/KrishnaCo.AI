document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const supabaseUrl = 'YOUR_SUPABASE_URL'
    const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY'
    const supabase = supabase.createClient(supabaseUrl, supabaseAnonKey)
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        alert('Please enter both username and password');
        return;
    }

    try {
        // Check if user exists and verify password
        const {  user, error } = await supabase
            .from('users')
            .select('username, name')
            .eq('username', username)
            .single();

        if (error) {
            if (error.code === 'PGRST116') {
                alert('User not found');
            } else {
                throw error;
            }
            return;
        }

        // Send login request to your Flask backend
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                username, 
                password
            }),
        });

        const data = await response.json();
        
        if (data.success) {
            // Store user info in localStorage if needed
            localStorage.setItem('currentUser', JSON.stringify({
                username: user.username,
                name: user.name
            }));
            
            // Redirect to home page or dashboard
            window.location.href = '/';
        } else {
            alert(data.message || 'Invalid credentials');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'An error occurred during login');
    }
});