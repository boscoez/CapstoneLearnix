import { useRouter } from 'next/router';
import { ReactNode, useState } from 'react';
import TopBar from "./topbar";
import SideBar from "./sidebar";
import FullScreenSearch from "./fullscreenSearch";
import SearchQuery from '../class/searchQuery';
import { getSearchHistory, getSearchQuery, makeLatestSearchQuery, pushSearchHistory, setSearchQuery } from '../_app';

interface LayoutProps {
    children: ReactNode;
}

const testQuery = new SearchQuery("What is love?", "Baby don't hurt me\n\
Don't hurt me\n\
No more");

const Layout: React.FC<LayoutProps> = ({ children }) => {
    // LOGIC:
    //   - If no search query was made, just display the welcome page
    //   - Else, 
    //      - If the app is currently waiting for the search results, display the prompt and the loading spinner below it
    //      - If the search results are ready, display the search results
    //      - If the app is loading an old search query, display a loading screen

    // TODO: Redirect to the welcomePage if the user is not logged in
    const router = useRouter();
    // useEffect(() => {
    //     const isLoggedIn = localStorage.getItem('loggedIn') === 'true'; // Your authentication logic here
    //     if (!isLoggedIn) {
    //         router.push('/welcomePage');
    //     }
    // }, []);

    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isSearchOpen, setIsSearchOpen] = useState(false);

    // Sidebar overlay behavior
    const toggleSidebar = () => {
      setIsSidebarOpen(!isSidebarOpen);
    };
  
    const sidebarClose = () => {
      setIsSidebarOpen(false);
    };

    const sidebarSearchQuery = (x: number) => {
        makeLatestSearchQuery(x);
        sidebarClose();
        router.push('/resultsPage');
    }

    const sidebarHome = () => {
        sidebarClose();
        router.push('/');
    }

    const sidebarLogout = () => {
        sidebarClose();
        // localStorage.setItem('loggedIn', 'false');
        window.location.reload();
        router.push('/welcomePage');
    }

    // Search overlay behavior
    const toggleSearch = () => {
        setIsSearchOpen(!isSearchOpen);
    };

    const closeSearch = () => {
        // TODO: Clear the search prompt textarea upon closing the search overlay
        setIsSearchOpen(false);
    };

    const doSearch = (x: string) => {
        closeSearch();

        var query = new SearchQuery(x, 
            "Eligendi totam ipsam quo a eligendi quisquam at. In voluptatum incidunt saepe. Mollitia aspernatur eos aliquam consectetur molestiae. Dolores cupiditate neque a." +
            "Voluptatem molestiae aut aut fugiat. Nobis et et veniam eaque est. Vel quibusdam dicta et qui iure quis magni. Dolorum fuga commodi omnis distinctio. Quia vel delectus et voluptatem et sed aliquam. Ea dolore doloremque et architecto voluptatem." +
            "Harum sint ut qui sed omnis molestiae amet sed. Delectus et commodi veniam natus repudiandae in. Voluptatem velit beatae magni. Delectus unde qui tenetur tempora. Ea cupiditate culpa suscipit est in adipisci. Praesentium facere non alias quia." +
            "Repudiandae sapiente dolorum cum perferendis laborum consequuntur nihil et. Est assumenda unde et aut ut. Et dolore ut omnis et aliquam aliquid. Dolor ratione rerum quisquam tempora ut illo." +
            "Pariatur fugit culpa placeat culpa. Velit fugiat eaque ut eum. Et quia est consequatur hic. Unde consequatur possimus culpa voluptatibus voluptas unde ab beatae. Ipsum est qui similique iure vel et quos molestiae. Iusto non a perspiciatis occaecati corporis ad laborum."
        );
        pushSearchHistory(query);
        // searchStateFunction(SearchStatus.READY);
        router.push('/resultsPage');
    }

    return (
        <div className="App">
            <TopBar onMenuClick={toggleSidebar} onSearchClick={toggleSearch} />
            <SideBar isOpen={isSidebarOpen} 
                onClose={sidebarClose} 
                onQueryClick={(x: number) => sidebarSearchQuery(x)}
                onHomeClick={sidebarHome} 
                onLogoutClick={sidebarLogout}/>
            <FullScreenSearch isOpen={isSearchOpen} onClose={closeSearch} onSearch={doSearch} />
            {children}
        </div>
    );
};

export default Layout;