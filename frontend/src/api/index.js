import axios from "axios";
import router from "@/router";
import store from "@/store";
import { jwtDecode } from "jwt-decode";

/**
 * Gets a valid access token or refreshes if needed
 * Uses a consistent 5-minute threshold for token expiration
 */
async function get_access_token() {
    // If we don't have tokens in the store, return null
    if (!store.state.jwt || !store.state.jwt.access) {
        return null;
    }

    try {
        const access = jwtDecode(store.state.jwt.access);
        const now = Date.now() / 1000;
        const refreshThreshold = 300; // 5 minutes in seconds

        // If token is about to expire, refresh it
        if (access.exp - now < refreshThreshold) {
            try {
                // Wait for the token to refresh
                await store.dispatch('refreshToken');
                return store.state.jwt.access;
            } catch (error) {
                console.error('Failed to refresh token:', error);
                return null;
            }
        }

        return store.state.jwt.access;
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
}

const axios_jwt = axios.create();

// Add CSRF token to all requests if using cookies for authentication
axios_jwt.interceptors.request.use(function(config) {
    // Get CSRF token from cookie if it exists
    const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }

    return config;
});

// Add JWT token to all requests
axios_jwt.interceptors.request.use(async function (config) {
    const access_token = await get_access_token();

    if (access_token) {
        config.headers.Authorization = "Bearer " + access_token;
    } else if (!router.currentRoute.value.fullPath.includes('login')) {
        // Only redirect if we're not already on the login page
        router.push({
            name: 'login',
            query: {
                next: router.currentRoute.value.fullPath,
                error: 'Please log in to continue'
            }
        });
    }

    return config;
}, function (error) {
    return Promise.reject(error);
});

export default axios_jwt
