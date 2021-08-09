import React from 'react';
import { Button, Card, Col, Rate, Row, Select, Spin, Typography } from 'antd';
import debounce from 'lodash/debounce';
import './App.css';

const { Meta } = Card;
const { Paragraph } = Typography;

function DebounceSelect({ fetchOptions, debounceTimeout = 200, ...props }) {
  const [fetching, setFetching] = React.useState(false);
  const [options, setOptions] = React.useState([]);
  const fetchRef = React.useRef(0);
  const debounceFetcher = React.useMemo(() => {
    const loadOptions = (value) => {
      fetchRef.current += 1;
      const fetchId = fetchRef.current;
      setOptions([]);
      setFetching(true);
      fetchOptions(value).then((newOptions) => {
        if (fetchId !== fetchRef.current) {
          return;
        }
        setOptions(newOptions);
        setFetching(false);
      });
    };

    return debounce(loadOptions, debounceTimeout);
  }, [fetchOptions, debounceTimeout]);

  return (
    <Select
      labelInValue
      filterOption={false}
      onSearch={debounceFetcher}
      notFoundContent={fetching ? <Spin size="small" /> : null}
      {...props}
      options={options}
    />
  );
}

async function fetchGames(query) {
  return fetch('/api/games?' + new URLSearchParams({
    q: query,
  }))
    .then((response) => response.json())
    .then((body) =>
      body.results.map((game) => ({
        label: game.name,
        value: game.appID,
      })),
    );
}

async function recommendGames(query_game_ids) {
  return fetch('/api/recommend', {
    body: JSON.stringify({
      games: query_game_ids,
    }),
    headers: {
      'content-type': 'application/json'
    },
    method: 'POST',
  })
    .then((response) => response.json());
}

async function recordAction(session, game, action, score = 0) {
  return fetch('/api/record', {
    body: JSON.stringify({
      engine: session.engine,
      queries: session.queries.map(g => g.appID),
      game: game,
      action: action,
      score: score,
    }),
    headers: {
      'content-type': 'application/json'
    },
    method: 'POST',
  })
    .then((response) => response.json());
}


function GameCard({ session, appID, name, description }) {
  const [rated, setRated] = React.useState(false);
  return (
    <Card
      hoverable
      cover={<img
        alt={name}
        title="Open in Steam"
        src={`https://cdn.akamai.steamstatic.com/steam/apps/${appID}/header.jpg`}
        onClick={() => window.open(`https://store.steampowered.com/app/${appID}`)}
      />}
      onClick={() => recordAction(session, appID, "click")}
    >
      <Meta
        title={
          <span
            title="Open in Steam"
            onClick={() => window.open(`https://store.steampowered.com/app/${appID}`)}
          >
            {name}
          </span>}
        description={
          <div>
            <Paragraph ellipsis={{ rows: 6, expandable: true }}>{description}</Paragraph>
            <div>{rated ? "Thank you!" : "Do you like it?"}</div>
            <Rate
              disabled={rated}
              onChange={value => {
                setRated(true);
                recordAction(session, appID, "rate", value)
              }}
            />
          </div>
        }
      />
    </Card>
  );
}

function GameList({ session, gameList }) {
  return (
    <div>
      <Row gutter={[16, 16]}>
        {gameList.map(game => (
          <Col key={session.timestamp + game.appID} xs={24} sm={12} md={8}>
            <GameCard session={session} {...game} />
          </Col>
        ))}
      </Row>
    </div>
  );
}

function App() {
  const [queryGames, setQueryGames] = React.useState([]);
  const [session, setSession] = React.useState(null);
  const [recommendedGames, setRecommendedGames] = React.useState([])

  return (
    <div className="App">
      <h1>Steam Game Recommender</h1>
      <Row>
        <Col xs={16} sm={18} md={20}>
          <DebounceSelect
            mode="multiple"
            value={queryGames}
            placeholder="Select 3 games to start recommendation"
            fetchOptions={fetchGames}
            onChange={(games) => {
              setQueryGames(games);
            }}
            style={{
              width: '100%',
            }}
          />
        </Col>
        <Col xs={8} sm={6} md={4}>
          <Button type="primary" disabled={queryGames.length < 3} onClick={() => {
            recommendGames(queryGames.map(g => g.value))
              .then(body => {
                setSession({
                  timestamp: Date.now(),
                  engine: body.engine,
                  queries: body.queries,
                });
                setRecommendedGames(body.results);
              });
          }}>Recommend</Button>
        </Col>
      </Row>
      <div style={{ height: 24 }}></div>
      <GameList session={session} gameList={recommendedGames} />
    </div>
  );
}

export default App;
