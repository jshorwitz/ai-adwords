"""Remove Streamlit from the project and clean up dependencies."""

import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_streamlit_from_project():
    """Remove Streamlit components from the project."""
    logger.info("🧹 Removing Streamlit from the project")
    logger.info("=" * 60)
    
    changes_made = []
    
    # 1. Update BigQuery client to remove Streamlit dependency
    logger.info("📝 Updating BigQuery client to remove Streamlit dependency...")
    
    bigquery_file = "/Users/joelhorwitz/dev/synter/ai-adwords/src/ads/bigquery_client.py"
    
    try:
        with open(bigquery_file, 'r') as f:
            content = f.read()
        
        # Remove streamlit import and related code
        new_content = content.replace('import streamlit as st', '')
        
        # Remove streamlit secrets handling section
        streamlit_section_start = '# Streamlit Cloud (secrets) — support both nested and root keys'
        streamlit_section_end = '# If no project_id found in secrets, fall through to env handling'
        
        lines = new_content.split('\n')
        new_lines = []
        skip = False
        
        for line in lines:
            if streamlit_section_start in line:
                skip = True
                continue
            elif streamlit_section_end in line:
                skip = False
                continue
            elif not skip:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        # Clean up any remaining streamlit references
        new_content = new_content.replace('if hasattr(st, "secrets") and st.secrets:', 'if False:  # Streamlit removed')
        
        with open(bigquery_file, 'w') as f:
            f.write(new_content)
        
        changes_made.append("✅ Updated BigQuery client")
        logger.info("✅ Updated BigQuery client to remove Streamlit dependency")
        
    except Exception as e:
        logger.error(f"❌ Failed to update BigQuery client: {e}")
    
    # 2. Remove/rename Streamlit dashboard
    dashboard_dir = "/Users/joelhorwitz/dev/synter/ai-adwords/src/dashboard"
    
    if os.path.exists(dashboard_dir):
        logger.info("📁 Moving Streamlit dashboard to backup location...")
        
        try:
            import shutil
            backup_dir = "/Users/joelhorwitz/dev/synter/ai-adwords/src/dashboard_backup_streamlit"
            shutil.move(dashboard_dir, backup_dir)
            changes_made.append("✅ Moved Streamlit dashboard to backup")
            logger.info("✅ Moved dashboard to backup location")
        except Exception as e:
            logger.error(f"❌ Failed to move dashboard: {e}")
    
    # 3. Remove .streamlit directory
    streamlit_dir = "/Users/joelhorwitz/dev/synter/ai-adwords/.streamlit"
    
    if os.path.exists(streamlit_dir):
        logger.info("📁 Removing .streamlit configuration directory...")
        
        try:
            import shutil
            shutil.rmtree(streamlit_dir)
            changes_made.append("✅ Removed .streamlit directory")
            logger.info("✅ Removed .streamlit directory")
        except Exception as e:
            logger.error(f"❌ Failed to remove .streamlit directory: {e}")
    
    # 4. Update requirements.txt
    requirements_file = "/Users/joelhorwitz/dev/synter/ai-adwords/requirements.txt"
    
    if os.path.exists(requirements_file):
        logger.info("📝 Updating requirements.txt to remove Streamlit...")
        
        try:
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
            
            new_lines = [line for line in lines if not line.strip().startswith('streamlit')]
            
            with open(requirements_file, 'w') as f:
                f.writelines(new_lines)
            
            changes_made.append("✅ Updated requirements.txt")
            logger.info("✅ Updated requirements.txt")
            
        except Exception as e:
            logger.error(f"❌ Failed to update requirements.txt: {e}")
    
    # 5. Update pyproject.toml
    pyproject_file = "/Users/joelhorwitz/dev/synter/ai-adwords/pyproject.toml"
    
    if os.path.exists(pyproject_file):
        logger.info("📝 Updating pyproject.toml to remove Streamlit...")
        
        try:
            with open(pyproject_file, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            new_lines = [line for line in lines if 'streamlit' not in line.lower()]
            
            new_content = '\n'.join(new_lines)
            
            with open(pyproject_file, 'w') as f:
                f.write(new_content)
            
            changes_made.append("✅ Updated pyproject.toml")
            logger.info("✅ Updated pyproject.toml")
            
        except Exception as e:
            logger.error(f"❌ Failed to update pyproject.toml: {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 Streamlit Removal Summary:")
    
    for change in changes_made:
        logger.info(f"  {change}")
    
    if changes_made:
        logger.info("\n💡 Next steps:")
        logger.info("  1. Test BigQuery connection: python verify_env_config.py")
        logger.info("  2. Reinstall dependencies: pip install -r requirements.txt")
        logger.info("  3. The project now uses only .env files for configuration")
        
        logger.info("\n📊 Benefits of removing Streamlit:")
        logger.info("  ✅ Simplified configuration (no more .streamlit/secrets.toml)")
        logger.info("  ✅ Reduced dependencies")
        logger.info("  ✅ Cleaner BigQuery client code")
        logger.info("  ✅ Only .env file configuration needed")
    else:
        logger.warning("⚠️  No changes were made - check for errors above")

if __name__ == "__main__":
    remove_streamlit_from_project()
