import React, { useEffect } from 'react';
// To use Auth0, you'll need to install the Auth0 React SDK:
// npm install @auth0/auth0-react
// or
// yarn add @auth0/auth0-react
//
// Then, in your main index.js or main.jsx file, you need to wrap your <App />
// component with the Auth0Provider like this:




// --- Reusable Icon Components ---
const HeartIcon = () => (
    <svg className="h-8 w-8 text-teal-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
    </svg>
);

const VisionIcon = () => (
    <svg className="h-6 w-6 text-teal-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
);

const MissionIcon = () => (
    <svg className="h-6 w-6 text-teal-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9a9.75 9.75 0 1111.46-8.883a12.75 12.75 0 01-1.46 9.383M16.5 18.75a9.75 9.75 0 00-9-9.75m9 9.75c0 1.146-.233 2.232-.656 3.223M4.5 9.75a9.75 9.75 0 019-9.75m-9 9.75a9.75 9.75 0 009 9.75" />
    </svg>
);


// --- Header and Auth Buttons ---
const Header = () => {
    const { loginWithRedirect, logout, user, isAuthenticated } = useAuth0();

    const handleSignUp = () => loginWithRedirect({
        authorizationParams: {
            screen_hint: 'signup',
        }
    });

    return (
        <header className="sticky top-0 bg-gray-900/50 backdrop-blur-lg border-b border-gray-800 z-10">
            <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
                <div className="flex items-center space-x-3">
                    <HeartIcon />
                    <span className="text-2xl font-bold text-white">Sehath Saathi</span>
                </div>
                <div className="space-x-4">
                    {!isAuthenticated ? (
                        <>
                            <button onClick={() => loginWithRedirect()} className="px-5 py-2 text-sm font-medium text-white bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">Login</button>
                            <button onClick={handleSignUp} className="px-5 py-2 text-sm font-medium text-white bg-teal-600 rounded-lg hover:bg-teal-500 transition-colors">Signup</button>
                        </>
                    ) : (
                         <div className="flex items-center space-x-4">
                            <span className="text-white hidden sm:inline">Welcome, {user.name || user.email}</span>
                            <button onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })} className="px-5 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-500 transition-colors">Logout</button>
                         </div>
                    )}
                </div>
            </nav>
        </header>
    );
};


// --- Main Page Sections ---
const HeroSection = () => {
    const { loginWithRedirect } = useAuth0();
    const handleGetStarted = () => loginWithRedirect({
        authorizationParams: {
            screen_hint: 'signup',
        }
    });

    return (
        <section className="py-20 md:py-32">
            <div className="container mx-auto px-6 text-center">
                <h1 className="text-4xl md:text-6xl font-extrabold leading-tight text-white">
                    Peace of mind, <span className="bg-gradient-to-r from-teal-400 to-green-400 text-transparent bg-clip-text">delivered.</span>
                </h1>
                <p className="mt-6 max-w-2xl mx-auto text-lg text-gray-300">
                    Sehath Saathi is the bridge across the distance. We provide a simple, reliable way for you to manage your parents' health and medication, no matter how far away you are.
                </p>
                <div className="mt-10">
                    <button onClick={handleGetStarted} className="bg-teal-600 text-white font-semibold py-3 px-8 rounded-lg shadow-lg hover:bg-teal-500 transform hover:-translate-y-1 transition-all">
                        Get Started for Free
                    </button>
                </div>
            </div>
        </section>
    );
};

const FeaturesSection = () => (
    <section className="py-20 bg-gray-900">
        <div className="container mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12">
                {/* Vision Card */}
                <div className="bg-gray-800 p-8 rounded-xl shadow-lg border border-gray-700 transform hover:scale-105 transition-transform duration-300">
                    <div className="flex items-center space-x-4 mb-4">
                        <div className="p-3 bg-gray-700 rounded-full">
                            <VisionIcon />
                        </div>
                        <h2 className="text-3xl font-bold text-white">Our Vision</h2>
                    </div>
                    <p className="text-gray-300 text-lg leading-relaxed">
                        Connecting parents with their children. Fostering a support system that goes beyond general healthcare, recreating the bond of a joint family, virtually.
                    </p>
                </div>

                {/* Mission Card */}
                <div className="bg-gray-800 p-8 rounded-xl shadow-lg border border-gray-700 transform hover:scale-105 transition-transform duration-300">
                    <div className="flex items-center space-x-4 mb-4">
                        <div className="p-3 bg-gray-700 rounded-full">
                            <MissionIcon />
                        </div>
                        <h2 className="text-3xl font-bold text-white">Our Mission</h2>
                    </div>
                    <p className="text-gray-300 text-lg leading-relaxed">
                        To make every senior citizen feel secure, connected, and supported. We want to ensure they never feel that they are alone in managing their health.
                    </p>
                </div>
            </div>
        </div>
    </section>
);

const Footer = () => (
    <footer className="bg-gray-900 border-t border-gray-800">
        <div className="container mx-auto px-6 py-8 text-center text-gray-400">
            <p>&copy; 2025 Sehath Saathi. All rights reserved.</p>
            <p className="text-sm mt-2">Made with ❤️ for families everywhere.</p>
        </div>
    </footer>
);


// --- Main App Component ---
function App() {
    const { isAuthenticated, isLoading, user } = useAuth0();

    // A simple effect to show a welcome alert after login
    // In a real app, you would redirect to a dashboard here.
    useEffect(() => {
        if (isAuthenticated && !isLoading) {
             // You can add a welcome notification here, or redirect.
             // For now, let's just log to the console.
             console.log(`Welcome, ${user.name || user.email}!`);
        }
    }, [isAuthenticated, isLoading, user]);


    return (
        <div className="min-h-screen flex flex-col bg-gray-900 text-gray-100 font-sans">
            <Header />
            <main className="flex-grow">
                <HeroSection />
                <FeaturesSection />
            </main>
            <Footer />
        </div>
    );
}

export default App;
