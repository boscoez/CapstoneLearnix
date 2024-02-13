import React from 'react';
import SearchQuery from '../class/searchQuery';
import { getSearchHistory } from '../_app';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onQueryClick: (x: number) => void;
  onLogoutClick: () => void;
  onHomeClick: () => void;
}

// TODO: Make the search query buttons into components
const SideBar: React.FC<SidebarProps> = ({ isOpen, onClose, onQueryClick, onHomeClick, onLogoutClick }) => {
    // This is so the buttons is sorted from up to down, latest to oldest
    var history = getSearchHistory().slice().reverse();
    var historyInd: number[] = [];
    history.forEach((query, index) => {
        historyInd.push(index);
    });
    historyInd = historyInd.slice().reverse();
    var dom: JSX.Element[] = [];
    history.forEach((query, index) => {
        dom.push(<button className="search-query-btn" key={historyInd[index]} onClick={() => onQueryClick(historyInd[index])}><i className="fi fi-br-search"></i><text>{query.getPrompt()}</text></button>);
    });

    return (
        <>
            <div className={`sidebar-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}></div>
            <div className={`sidebar ${isOpen ? 'open' : ''}`}>
                <div className="top-btns">
                    <button className="close-btn" onClick={onClose}>
                        <i className="fi fi-rr-menu-burger"></i><text>LEARNIX</text>
                    </button>
                    {dom}
                </div>
                <div className="bottom-btns">
                    <button onClick={onLogoutClick}><i className="fi fi-rr-exit"></i><text>Logout</text></button>
                    <button onClick={onHomeClick}><i className="fi fi-rr-home"></i><text>Home</text></button>
                </div>
            </div>
        </>
    );
};

export default SideBar;