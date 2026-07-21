export const isAuthenticated = () => true;
export const getToken = () => 'fake-token';
export const login = () => Promise.resolve({ success: true });
export const logout = () => {};