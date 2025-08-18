# AI Code Audit System - Configuration Guide

## 📋 Overview

This guide explains how to configure the AI Code Audit System with the correct API keys and model settings.

## 🔧 Configuration Files

### Main Configuration File: `config.yaml`

The system uses a YAML configuration file located in the project root:

```yaml
# Database Configuration
database:
  host: "localhost"
  port: 3306
  username: "root"
  password: "jackhou."
  database: "ai_code_audit_system"

# LLM Configuration
llm:
  default_model: "qwen-turbo"
  
  # Qwen Provider (SiliconFlow)
  qwen:
    api_key: "sk-bldkmthquuuypfythtasqvdhwtclplekygnbylvboctetkeh"
    base_url: "https://api.siliconflow.cn/v1"
    model_name: "Qwen/Qwen2.5-7B-Instruct"
    enabled: true
    priority: 1
  
  # Kimi Provider (SiliconFlow)
  kimi:
    api_key: "sk-kpepqjjtmxpcdhqcvrdekuroxvmpmphkfouhzbcbudbpzzzt"
    base_url: "https://api.siliconflow.cn/v1"
    model_name: "moonshot-v1-8k"
    enabled: true
    priority: 2
```

## 🤖 Supported Models

### Qwen Models (through SiliconFlow)
- **qwen-turbo**: `Qwen/Qwen2.5-7B-Instruct` (32K context)
- **qwen-plus**: `Qwen/Qwen2.5-14B-Instruct` (32K context)
- **qwen-max**: `Qwen/Qwen2.5-72B-Instruct` (32K context)
- **qwen-coder**: `Qwen/Qwen2.5-Coder-7B-Instruct` (32K context)

### Kimi Models (through SiliconFlow)
- **kimi-8k**: `moonshot-v1-8k` (8K context)
- **kimi-32k**: `moonshot-v1-32k` (32K context)
- **kimi-128k**: `moonshot-v1-128k` (128K context)

## 🔑 API Configuration

### Important Notes:
1. **Both providers use SiliconFlow API**: `https://api.siliconflow.cn/v1`
2. **Same API key can be used for both**: The system supports using the same SiliconFlow API key for both Qwen and Kimi models
3. **Model names are specific**: Use the exact model names as specified above

### Environment Variables (Alternative)

You can also configure using environment variables:

```bash
export QWEN_API_KEY="sk-bldkmthquuuypfythtasqvdhwtclplekygnbylvboctetkeh"
export KIMI_API_KEY="sk-kpepqjjtmxpcdhqcvrdekuroxvmpmphkfouhzbcbudbpzzzt"
export QWEN_BASE_URL="https://api.siliconflow.cn/v1"
export KIMI_BASE_URL="https://api.siliconflow.cn/v1"
```

## 📝 Analysis Templates

### Available Templates:
1. **security_audit**: Comprehensive security vulnerability analysis
2. **code_review**: Code quality and best practices review
3. **vulnerability_scan**: Targeted vulnerability scanning

### Template Variables:
- **security_audit**: `language`, `file_path`, `project_type`, `dependencies`, `code_content`, `additional_context`
- **code_review**: `language`, `file_path`, `target_element`, `context`, `code_content`
- **vulnerability_scan**: `language`, `file_path`, `entry_points`, `input_sources`, `code_content`, `frameworks`

## 🚀 Usage Examples

### View Configuration
```bash
python -m ai_code_audit.cli.main config
python -m ai_code_audit.cli.main config --show-keys
```

### Run Security Audit
```bash
# Using Qwen model
python -m ai_code_audit.cli.main audit . --max-files 3 --model qwen-turbo

# Using Kimi model
python -m ai_code_audit.cli.main audit . --max-files 3 --model kimi-8k

# Different templates
python -m ai_code_audit.cli.main audit . --template code_review --model qwen-plus
python -m ai_code_audit.cli.main audit . --template vulnerability_scan --model kimi-32k
```

### Save Results
```bash
python -m ai_code_audit.cli.main audit . --max-files 5 --output-file results.json
```

## 🔍 Testing Configuration

### Test Configuration Loading
```bash
python test_config_system.py
```

### Test Model Configurations
```bash
python test_corrected_models.py
```

### Test LLM Integration
```bash
python test_llm_integration.py
```

## 🛠️ Troubleshooting

### Common Issues:

1. **API Key Invalid**
   - Verify API key is correct
   - Check if key has sufficient credits
   - Ensure key is for SiliconFlow platform

2. **Model Not Found**
   - Verify model names match exactly
   - Check if model is available on SiliconFlow
   - Try different model variant

3. **Rate Limiting**
   - Reduce `max_files` parameter
   - Increase delays between requests
   - Check rate limits in configuration

4. **Configuration Not Found**
   - Ensure `config.yaml` exists in project root
   - Check file permissions
   - Verify YAML syntax

### Debug Mode:
```bash
python -m ai_code_audit.cli.main --debug audit . --max-files 1
```

## 📊 Performance Tips

### Model Selection:
- **qwen-turbo**: Fast, cost-effective for basic analysis
- **qwen-plus**: Better quality for detailed analysis
- **qwen-max**: Highest quality for complex code
- **kimi-128k**: Best for large files with long context

### Optimization:
- Use `--max-files` to limit analysis scope
- Choose appropriate model based on file complexity
- Use `vulnerability_scan` for focused security analysis
- Use `code_review` for quality assessment

## 🔐 Security Considerations

1. **API Key Protection**
   - Store keys in configuration file with restricted permissions
   - Use environment variables in production
   - Never commit API keys to version control

2. **Data Privacy**
   - Code is sent to SiliconFlow API for analysis
   - Review privacy policies before use
   - Consider using local models for sensitive code

3. **Access Control**
   - Restrict access to configuration files
   - Use separate API keys for different environments
   - Monitor API usage and costs

## 📈 Cost Management

### Token Usage:
- **qwen-turbo**: ~$0.001 per 1K tokens
- **qwen-plus**: ~$0.002 per 1K tokens
- **kimi models**: ~$0.001-0.005 per 1K tokens

### Cost Optimization:
- Limit file size with `max_file_size` setting
- Use appropriate context length models
- Monitor usage with `--show-tokens` option
- Set budget alerts on SiliconFlow platform

## 🔄 Configuration Updates

### Updating API Keys:
1. Edit `config.yaml` file
2. Or set environment variables
3. Restart application
4. Verify with `config` command

### Adding New Models:
1. Update model definitions in `base.py`
2. Add provider support
3. Update CLI options
4. Test with new configuration

## 📞 Support

For issues with:
- **Configuration**: Check this guide and test scripts
- **API Keys**: Contact SiliconFlow support
- **Models**: Verify model availability on SiliconFlow
- **System**: Check logs and use debug mode
