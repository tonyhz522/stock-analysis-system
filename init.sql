-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default users (使用明文密码，应用程序会处理)
INSERT INTO users (username, password, name) VALUES
('admin', 'password123', 'Administrator'),
('user1', 'password123', 'User One'),
('user2', 'password123', 'User Two');

-- Create stock data table
CREATE TABLE IF NOT EXISTS stock_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10, 2) NOT NULL,
    close_price DECIMAL(10, 2) NOT NULL,
    high_price DECIMAL(10, 2) NOT NULL,
    low_price DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    INDEX idx_stock_date (stock_code, date)
);

-- Create procedure to generate stock data
DELIMITER //

CREATE PROCEDURE generate_stock_data()
BEGIN
    DECLARE start_date DATE DEFAULT '2020-01-01';
    DECLARE end_date DATE DEFAULT CURDATE();
    DECLARE curr_date DATE;
    DECLARE stock_index INT DEFAULT 0;
    DECLARE stock_code VARCHAR(10);
    DECLARE base_price DECIMAL(10, 2);
    DECLARE volatility DECIMAL(5, 3);
    DECLARE trend DECIMAL(5, 3);
    DECLARE prev_close DECIMAL(10, 2);
    DECLARE daily_return DECIMAL(5, 3);
    DECLARE open_price DECIMAL(10, 2);
    DECLARE close_price DECIMAL(10, 2);
    DECLARE high_price DECIMAL(10, 2);
    DECLARE low_price DECIMAL(10, 2);
    DECLARE volume BIGINT;
    
    -- Clear existing data
    TRUNCATE TABLE stock_data;
    
    -- Define stocks with different characteristics
    WHILE stock_index < 5 DO
        CASE stock_index
            WHEN 0 THEN 
                SET stock_code = 'AAPL';
                SET base_price = 150.00;
                SET volatility = 0.02;
                SET trend = 0.0003;
            WHEN 1 THEN 
                SET stock_code = 'GOOGL';
                SET base_price = 2800.00;
                SET volatility = 0.025;
                SET trend = 0.0002;
            WHEN 2 THEN 
                SET stock_code = 'MSFT';
                SET base_price = 300.00;
                SET volatility = 0.018;
                SET trend = 0.0004;
            WHEN 3 THEN 
                SET stock_code = 'AMZN';
                SET base_price = 3300.00;
                SET volatility = 0.03;
                SET trend = 0.0001;
            WHEN 4 THEN 
                SET stock_code = 'TSLA';
                SET base_price = 800.00;
                SET volatility = 0.05;
                SET trend = 0.0005;
        END CASE;
        
        SET curr_date = start_date;
        SET prev_close = base_price;
        
        -- Generate daily data for each stock
        WHILE curr_date <= end_date DO
            -- Skip weekends
            IF DAYOFWEEK(curr_date) NOT IN (1, 7) THEN
                -- Generate random daily return with trend
                SET daily_return = (RAND() - 0.5) * 2 * volatility + trend;
                
                -- Calculate prices
                SET open_price = prev_close * (1 + (RAND() - 0.5) * volatility * 0.5);
                SET close_price = prev_close * (1 + daily_return);
                SET high_price = GREATEST(open_price, close_price) * (1 + RAND() * volatility * 0.3);
                SET low_price = LEAST(open_price, close_price) * (1 - RAND() * volatility * 0.3);
                SET volume = 10000000 + ROUND(RAND() * 5000000);
                
                -- Insert data
                INSERT INTO stock_data (stock_code, date, open_price, close_price, high_price, low_price, volume)
                VALUES (stock_code, curr_date, open_price, close_price, high_price, low_price, volume);
                
                SET prev_close = close_price;
            END IF;
            
            SET curr_date = DATE_ADD(curr_date, INTERVAL 1 DAY);
        END WHILE;
        
        SET stock_index = stock_index + 1;
    END WHILE;
END//

DELIMITER ;

-- Generate initial stock data
CALL generate_stock_data();